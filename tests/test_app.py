from pathlib import Path
import shutil
import sys
import types
import uuid

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.modules.setdefault("PyPDF2", types.SimpleNamespace(PdfReader=object))
sys.modules.setdefault("pdfplumber", types.SimpleNamespace(open=lambda *args, **kwargs: None))
sys.modules.setdefault("fitz", types.SimpleNamespace(open=lambda *args, **kwargs: None))

import app as app_module


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def test_healthz_reports_pdf_and_cache_counts(client, monkeypatch):
    cache_dir = PROJECT_ROOT / "tests_runtime_cache" / uuid.uuid4().hex
    try:
        cache_dir.mkdir(parents=True)
        (cache_dir / "one.json").write_text("{}", encoding="utf-8")
        (cache_dir / "two.json").write_text("{}", encoding="utf-8")
        (cache_dir / "ignore.txt").write_text("x", encoding="utf-8")

        monkeypatch.setattr(app_module, "CACHE_FOLDER", str(cache_dir))
        monkeypatch.setattr(app_module, "list_pdf_files", lambda: ["a.pdf", "b.pdf", "c.pdf"])

        response = client.get("/healthz")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["status"] == "ok"
        assert payload["pdf_count"] == 3
        assert payload["cache_count"] == 2
    finally:
        shutil.rmtree(cache_dir.parent, ignore_errors=True)


def test_api_search_reports_file_level_errors(client, monkeypatch):
    monkeypatch.setattr(app_module, "list_pdf_files", lambda: ["good.pdf", "bad.pdf"])

    def fake_get_pdf_text(pdf_path, force_refresh=False):
        if Path(pdf_path).name == "bad.pdf":
            raise RuntimeError("broken parser")
        return "contract clause", True

    monkeypatch.setattr(app_module, "get_pdf_text", fake_get_pdf_text)
    monkeypatch.setattr(app_module, "advanced_search", lambda text, query: ["match one", "match one", "match two"])
    monkeypatch.setattr(app_module, "rank_results", lambda matches, query: matches)

    response = client.post("/api/search", json={"query": "contract"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["total_matches"] == 2
    assert payload["files_with_matches"] == 1
    assert payload["matches_by_file"]["good.pdf"]["cache_hit"] is True
    assert payload["matches_by_file"]["good.pdf"]["count"] == 2
    assert "broken parser" in payload["matches_by_file"]["bad.pdf"]["error"]


def test_api_search_returns_partial_results_on_timeout(client, monkeypatch):
    monkeypatch.setattr(app_module, "list_pdf_files", lambda: ["slow-a.pdf", "slow-b.pdf"])
    monkeypatch.setattr(app_module, "get_pdf_text", lambda pdf_path, force_refresh=False: ("text", True))
    monkeypatch.setattr(app_module, "advanced_search", lambda text, query: [])
    monkeypatch.setattr(app_module, "rank_results", lambda matches, query: matches)

    time_values = iter([0.0, 0.0, 0.1, 0.2, 26.0, 26.1])
    monkeypatch.setattr(app_module.time, "monotonic", lambda: next(time_values))

    response = client.post("/api/search", json={"query": "delay"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["timed_out"] is True
    assert "Partial results" in payload["warning"]
