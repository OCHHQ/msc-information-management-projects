from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import hashlib
import io
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

from werkzeug.utils import secure_filename


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from extractor import extract_text_from_pdf
from search_engine import rank_results, advanced_search


def _int_from_env(name, default):
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError:
        return default


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ir-legal-search-dev-key")


UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "data"))
EXPORT_FOLDER = os.getenv("EXPORT_FOLDER", os.path.join(BASE_DIR, "exports"))
CACHE_FOLDER = os.getenv("CACHE_FOLDER", os.path.join(BASE_DIR, "cache", "pdf_text"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 16 * 1024 * 1024
SEARCH_TIMEOUT_SECONDS = _int_from_env("SEARCH_TIMEOUT_SECONDS", 25)
MAX_MATCHES_PER_FILE = _int_from_env("MAX_MATCHES_PER_FILE", 20)
MAX_PAGES_TO_EXTRACT = _int_from_env("MAX_PAGES_TO_EXTRACT", 0)
SEARCH_USES_ONLY_CACHED_TEXT = os.getenv("SEARCH_USES_ONLY_CACHED_TEXT", "1") == "1"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def configure_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger("ir_legal_search")


logger = configure_logging()
RUNNING_ON_RENDER = bool(os.getenv("RENDER")) or bool(os.getenv("RENDER_SERVICE_NAME"))


def ensure_runtime_directories():
    # Gunicorn imports the app directly, so these folders must exist before any request runs.
    for path in (UPLOAD_FOLDER, EXPORT_FOLDER, CACHE_FOLDER):
        os.makedirs(path, exist_ok=True)


ensure_runtime_directories()
if RUNNING_ON_RENDER:
    logger.info(
        "Render startup ready upload_folder=%s cache_folder=%s timeout=%ss max_matches=%s max_pages=%s",
        UPLOAD_FOLDER,
        CACHE_FOLDER,
        SEARCH_TIMEOUT_SECONDS,
        MAX_MATCHES_PER_FILE,
        MAX_PAGES_TO_EXTRACT or "all",
    )


def allowed_file(filename):
    """Check whether the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def list_pdf_files():
    if not os.path.isdir(UPLOAD_FOLDER):
        return []

    return sorted(
        file_name
        for file_name in os.listdir(UPLOAD_FOLDER)
        if file_name.lower().endswith(".pdf")
        and os.path.isfile(os.path.join(UPLOAD_FOLDER, file_name))
    )


def cache_path_for_pdf(pdf_path):
    digest = hashlib.sha1(os.path.abspath(pdf_path).encode("utf-8")).hexdigest()
    return os.path.join(CACHE_FOLDER, f"{digest}.json")


def load_cached_text(pdf_path):
    cache_path = cache_path_for_pdf(pdf_path)
    if not os.path.exists(cache_path):
        return None

    try:
        source_stats = os.stat(pdf_path)
        with open(cache_path, "r", encoding="utf-8") as cache_file:
            cached = json.load(cache_file)

        # Reuse cached text only when the source PDF has not changed on disk.
        if (
            cached.get("source_mtime_ns") == source_stats.st_mtime_ns
            and cached.get("source_size") == source_stats.st_size
        ):
            return cached.get("text", "")
    except Exception as exc:
        logger.warning("Failed reading cache for %s: %s", pdf_path, exc)

    return None


def save_cached_text(pdf_path, text):
    source_stats = os.stat(pdf_path)
    payload = {
        "source_path": os.path.abspath(pdf_path),
        "source_mtime_ns": source_stats.st_mtime_ns,
        "source_size": source_stats.st_size,
        "cached_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "text": text,
    }

    cache_path = cache_path_for_pdf(pdf_path)
    with open(cache_path, "w", encoding="utf-8") as cache_file:
        json.dump(payload, cache_file)


def get_pdf_text(pdf_path, force_refresh=False):
    if not force_refresh:
        cached_text = load_cached_text(pdf_path)
        if cached_text is not None:
            logger.info("PDF cache hit file=%s", os.path.basename(pdf_path))
            return cached_text, True

    # Extract once, then persist the text so later searches do not re-parse the same PDF.
    max_pages = MAX_PAGES_TO_EXTRACT if MAX_PAGES_TO_EXTRACT > 0 else None
    extraction_start = time.monotonic()
    extracted_text = extract_text_from_pdf(pdf_path, max_pages=max_pages)
    save_cached_text(pdf_path, extracted_text)
    logger.info(
        "PDF extracted file=%s chars=%s pages=%s duration=%.2fs",
        os.path.basename(pdf_path),
        len(extracted_text),
        max_pages or "all",
        time.monotonic() - extraction_start,
    )
    return extracted_text, False


def get_cached_pdf_text_only(pdf_path):
    cached_text = load_cached_text(pdf_path)
    if cached_text is None:
        raise RuntimeError(
            f"Document not indexed yet: {os.path.basename(pdf_path)}. "
            "Re-upload it or rebuild its cache before searching."
        )
    logger.info("PDF cache hit file=%s", os.path.basename(pdf_path))
    return cached_text


def classify_search_type(query):
    if '"' in query:
        return "phrase"
    if any(operator in query.upper() for operator in [" AND ", " OR ", " NOT "]):
        return "boolean"
    return "simple"


def trim_matches(matches):
    unique_matches = list(dict.fromkeys(matches))
    if len(unique_matches) > MAX_MATCHES_PER_FILE:
        return unique_matches[:MAX_MATCHES_PER_FILE], True
    return unique_matches, False


def search_across_pdfs(query):
    """Search across all PDFs with caching and timeout protection."""
    results = {
        "query": query,
        "total_matches": 0,
        "files_searched": 0,
        "files_with_matches": 0,
        "search_time": 0,
        "matches_by_file": {},
        "timed_out": False,
        "warning": None,
        "skipped_files": 0,
    }

    start_time = time.monotonic()
    pdf_files = list_pdf_files()
    results["files_searched"] = len(pdf_files)

    if not pdf_files:
        results["error"] = "No PDF files found in data folder"
        return results

    search_type = classify_search_type(query)

    for pdf_file in pdf_files:
        elapsed = time.monotonic() - start_time
        if elapsed >= SEARCH_TIMEOUT_SECONDS:
            # Return partial results instead of letting the request hang until the worker is killed.
            results["timed_out"] = True
            results["warning"] = (
                f"Search stopped after {SEARCH_TIMEOUT_SECONDS} seconds. Partial results are shown."
            )
            break

        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file)
        file_start = time.monotonic()

        try:
            if SEARCH_USES_ONLY_CACHED_TEXT:
                text = get_cached_pdf_text_only(pdf_path)
                cache_hit = True
            else:
                text, cache_hit = get_pdf_text(pdf_path)
            matches = advanced_search(text, query)

            if matches:
                ranked_matches = rank_results(matches, query)
                limited_matches, was_trimmed = trim_matches(ranked_matches)
                file_warning = None
                if was_trimmed:
                    file_warning = f"Showing first {MAX_MATCHES_PER_FILE} matches"

                results["matches_by_file"][pdf_file] = {
                    "matches": limited_matches,
                    "count": len(limited_matches),
                    "search_type": search_type,
                    "cache_hit": cache_hit,
                    "warning": file_warning,
                }
                results["total_matches"] += len(limited_matches)
                results["files_with_matches"] += 1
                logger.info(
                    "Search file processed file=%s cache_hit=%s raw_matches=%s returned_matches=%s duration=%.2fs query=%r",
                    pdf_file,
                    cache_hit,
                    len(matches),
                    len(limited_matches),
                    time.monotonic() - file_start,
                    query,
                )
            else:
                logger.info(
                    "Search file processed file=%s cache_hit=%s raw_matches=0 returned_matches=0 duration=%.2fs query=%r",
                    pdf_file,
                    cache_hit,
                    time.monotonic() - file_start,
                    query,
                )

        except Exception as exc:
            logger.exception(
                "Render diagnosis search failed file=%s duration=%.2fs query=%r",
                pdf_file,
                time.monotonic() - file_start,
                query,
            )
            results["matches_by_file"][pdf_file] = {
                "error": str(exc),
                "count": 0,
                "search_type": "error",
            }
            results["skipped_files"] += 1

    results["search_time"] = round(time.monotonic() - start_time, 2)
    if results["skipped_files"] > 0 and not results["warning"]:
        results["warning"] = (
            f"{results['skipped_files']} document(s) were skipped because they are not indexed yet."
        )
    logger.info(
        "Search completed query=%r files=%s matches=%s skipped=%s timeout=%s duration=%.2fs",
        query,
        results["files_searched"],
        results["total_matches"],
        results["skipped_files"],
        results["timed_out"],
        results["search_time"],
    )
    return results


def wants_json_response():
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    accept_header = request.headers.get("Accept", "")
    return "application/json" in accept_header


@app.route("/")
def index():
    """Main search page."""
    pdf_files = list_pdf_files()
    return render_template("index.html", pdf_files=pdf_files)


@app.route("/healthz")
def healthz():
    """Simple health check for Render monitoring."""
    pdf_files = list_pdf_files()
    cache_files = 0
    if os.path.isdir(CACHE_FOLDER):
        cache_files = len(
            [name for name in os.listdir(CACHE_FOLDER) if name.lower().endswith(".json")]
        )

    return jsonify(
        {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pdf_count": len(pdf_files),
            "cache_count": cache_files,
            "search_timeout_seconds": SEARCH_TIMEOUT_SECONDS,
            "max_matches_per_file": MAX_MATCHES_PER_FILE,
        }
    )


@app.route("/search", methods=["POST"])
def search():
    """Handle search requests."""
    query = request.form.get("query", "").strip()

    if not query:
        flash("Please enter a search query", "error")
        return redirect(url_for("index"))

    results = search_across_pdfs(query)
    return render_template("results.html", results=results)


@app.route("/api/search", methods=["POST"])
def api_search():
    """JSON search endpoint for AJAX requests."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    results = search_across_pdfs(query)
    return jsonify(results)


@app.route("/api/files")
def api_files():
    """List available PDF files."""
    files = []
    for pdf_file in list_pdf_files():
        file_path = os.path.join(UPLOAD_FOLDER, pdf_file)
        files.append(
            {
                "name": pdf_file,
                "size": f"{os.path.getsize(file_path) / 1024:.1f} KB",
            }
        )

    return jsonify(files)


@app.route("/export/<format>", methods=["POST"])
def export_results(format):
    """Export search results to different formats."""
    try:
        data = request.get_json() or {}
        query = data.get("query", "Unknown Query")
        results = data.get("results", [])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "txt":
            output = io.StringIO()
            output.write("IR LEGAL SEARCH RESULTS\n")
            output.write(f"{'=' * 70}\n")
            output.write(f"Query: {query}\n")
            output.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.write(f"Total Results: {len(results)}\n")
            output.write(f"{'=' * 70}\n\n")

            for index, result in enumerate(results, 1):
                output.write(f"Result {index}:\n")
                output.write(f"{result['text']}\n")
                output.write(f"Source: {result['filename']}\n")
                output.write(f"{'-' * 70}\n\n")

            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode("utf-8")),
                mimetype="text/plain",
                as_attachment=True,
                download_name=f"search_results_{timestamp}.txt",
            )

        if format == "csv":
            output = io.StringIO()
            output.write("Index,Filename,Match Text\n")

            for index, result in enumerate(results, 1):
                text = result["text"].replace('"', '""')
                filename = result["filename"].replace('"', '""')
                output.write(f'{index},"{filename}","{text}"\n')

            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode("utf-8")),
                mimetype="text/csv",
                as_attachment=True,
                download_name=f"search_results_{timestamp}.csv",
            )

        if format == "html":
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Search Results - {query}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #0d6efd; color: white; padding: 20px; border-radius: 8px; }}
        .result {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .result-header {{ color: #0d6efd; font-weight: bold; margin-bottom: 10px; }}
        .filename {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>IR Legal Search Results</h1>
        <p><strong>Query:</strong> {query}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Results:</strong> {len(results)}</p>
    </div>
"""

            for index, result in enumerate(results, 1):
                text = result["text"].replace("<", "&lt;").replace(">", "&gt;")
                html += f"""
    <div class="result">
        <div class="result-header">Result {index}</div>
        <div>{text}</div>
        <div class="filename">Source: {result['filename']}</div>
    </div>
"""

            html += """
</body>
</html>
"""

            return send_file(
                io.BytesIO(html.encode("utf-8")),
                mimetype="text/html",
                as_attachment=True,
                download_name=f"search_results_{timestamp}.html",
            )

        return jsonify({"error": "Invalid format"}), 400

    except Exception as exc:
        logger.exception("Export failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    """Handle file uploads."""
    if request.method == "POST":
        if "file" not in request.files:
            message = "No file selected"
            if wants_json_response():
                return jsonify({"success": False, "error": message}), 400
            flash(message, "error")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            message = "No file selected"
            if wants_json_response():
                return jsonify({"success": False, "error": message}), 400
            flash(message, "error")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            target_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            if os.path.exists(target_path):
                name, extension = os.path.splitext(filename)
                filename = f"{name}_{uuid.uuid4().hex[:8]}{extension}"
                target_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            file.save(target_path)

            try:
                # Build the text cache during upload so the first user search is much faster.
                get_pdf_text(target_path, force_refresh=True)
            except Exception as exc:
                logger.exception(
                    "Render diagnosis upload indexing failed file=%s size_bytes=%s",
                    filename,
                    os.path.getsize(target_path),
                )
                if wants_json_response():
                    return jsonify(
                        {
                            "success": False,
                            "error": f"File uploaded, but indexing failed: {exc}",
                        }
                    ), 500
                flash(f"File uploaded, but indexing failed: {exc}", "error")
                return redirect(url_for("index"))

            success_message = f"File {filename} uploaded and indexed successfully."
            if wants_json_response():
                return jsonify({"success": True, "filename": filename, "message": success_message})

            flash(success_message, "success")
            return redirect(url_for("index"))

        message = "Only PDF files are allowed"
        if wants_json_response():
            return jsonify({"success": False, "error": message}), 400
        flash(message, "error")

    return render_template("upload.html")


@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    """Delete uploaded file and its cache."""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "File not found"}), 404

        cache_path = cache_path_for_pdf(file_path)
        os.remove(file_path)
        if os.path.exists(cache_path):
            os.remove(cache_path)

        flash(f"Successfully deleted {filename}", "success")
        return jsonify({"success": True, "message": f"{filename} deleted"})

    except Exception as exc:
        logger.exception("Delete failed for %s", filename)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@app.route("/help")
def help():
    """Help page with search syntax."""
    return render_template("help.html")


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", error="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled server error: %s", error)
    return render_template("error.html", error="Internal server error"), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
