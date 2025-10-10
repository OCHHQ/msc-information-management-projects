// IR Legal Search Tool - JavaScript Functionality

document.addEventListener('DOMContentLoaded', function() {
    initializeSearchForm();
    initializeResultsPage();
    initializeFileUpload();
});

// Search Form Functionality
function initializeSearchForm() {
    const searchForm = document.getElementById('searchForm');
    const queryInput = document.getElementById('query');
    const exampleButtons = document.querySelectorAll('.example-query');
    
    // Add example query click handlers
    exampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const query = this.dataset.query;
            queryInput.value = query;
            queryInput.focus();
            
            // Add visual feedback
            button.classList.add('btn-primary');
            button.classList.remove('btn-outline-secondary');
            setTimeout(() => {
                button.classList.remove('btn-primary');
                button.classList.add('btn-outline-secondary');
            }, 300);
        });
    });
    
    // Search form submission with loading state
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalHTML = submitBtn.innerHTML;
            
            // Show loading state
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
            submitBtn.disabled = true;
            
            // Add loading class to form
            this.classList.add('loading');
        });
    }
    
    // Auto-complete functionality (basic)
    if (queryInput) {
        let searchTimeout;
        queryInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                suggestQueries(this.value);
            }, 300);
        });
    }
}

// Results Page Functionality
function initializeResultsPage() {
    // Auto-highlight search terms
    const resultsContainer = document.querySelector('.match-text');
    if (resultsContainer) {
        highlightAllMatches();
    }
    
    // Initialize collapse buttons
    initializeCollapseButtons();
    
    // Initialize copy buttons
    initializeCopyButtons();
}

// File Upload Functionality
function initializeFileUpload() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.querySelector('input[type="file"]');
    
    if (uploadArea && fileInput) {
        // Drag and drop functionality
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        uploadArea.addEventListener('drop', handleDrop, false);
        uploadArea.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', handleFileSelect);
    }
}

// Utility Functions
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    e.target.closest('.upload-area').classList.add('dragover');
}

function unhighlight(e) {
    e.target.closest('.upload-area').classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (file.type === 'application/pdf') {
            uploadFile(file);
        } else {
            showNotification('Only PDF files are allowed', 'error');
        }
    });
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Show progress
    const progressContainer = createProgressBar(file.name);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${file.name} uploaded successfully`, 'success');
            updateFileList();
        } else {
            showNotification(data.error || 'Upload failed', 'error');
        }
    })
    .catch(error => {
        showNotification('Upload failed: ' + error.message, 'error');
    })
    .finally(() => {
        progressContainer.remove();
    });
}

// Search Results Functions
function highlightAllMatches() {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query') || document.querySelector('[data-query]')?.dataset.query;
    
    if (query) {
        const matchElements = document.querySelectorAll('.match-text');
        matchElements.forEach((element, index) => {
            highlightText(element.id, query);
        });
    }
}

function highlightText(elementId, query) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const text = element.innerHTML;
    
    // Remove existing highlights
    const cleanText = text.replace(/<mark class="highlight">/g, '').replace(/<\/mark>/g, '');
    
    // Clean query (remove quotes and operators for highlighting)
    let searchTerms = query.replace(/['"]/g, '').replace(/\b(AND|OR|NOT)\b/gi, '').split(/\s+/).filter(term => term.length > 0);
    
    let highlightedText = cleanText;
    
    // Apply highlighting for each term
    searchTerms.forEach(term => {
        if (term.length > 2) {  // Only highlight terms longer than 2 characters
            const regex = new RegExp(`\\b(${escapeRegExp(term)})\\b`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark class="highlight">$1</mark>');
        }
    });
    
    element.innerHTML = highlightedText;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function initializeCollapseButtons() {
    const collapseButtons = document.querySelectorAll('[data-bs-toggle="collapse"]');
    collapseButtons.forEach(button => {
        const icon = button.querySelector('i');
        const target = button.dataset.bsTarget;
        
        button.addEventListener('click', function() {
            setTimeout(() => {
                const targetElement = document.querySelector(target);
                if (targetElement.classList.contains('show')) {
                    icon.className = 'fas fa-chevron-up';
                } else {
                    icon.className = 'fas fa-chevron-down';
                }
            }, 100);
        });
    });
}

function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('[onclick*="copyToClipboard"]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('onclick').match(/copyToClipboard\('([^']+)'\)/)[1];
            copyToClipboard(targetId);
        });
    });
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const text = element.innerText;
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            showCopyFeedback(element);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showCopyFeedback(element);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
        
        document.body.removeChild(textArea);
    }
}

function showCopyFeedback(element) {
    const button = document.querySelector(`[onclick*="${element.id}"]`);
    if (button) {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check text-success"></i>';
        button.classList.add('btn-success');
        button.classList.remove('btn-outline-secondary');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-secondary');
        }, 2000);
    }
}

// Export Functions
function exportResults(format) {
    const results = gatherResultsData();
    
    switch(format) {
        case 'txt':
            exportAsText(results);
            break;
        case 'csv':
            exportAsCSV(results);
            break;
        case 'html':
            exportAsHTML(results);
            break;
        default:
            console.error('Unknown export format:', format);
    }
}

function gatherResultsData() {
    const query = document.querySelector('[data-query]')?.dataset.query || 'Unknown Query';
    const matches = [];
    
    document.querySelectorAll('.match-text').forEach((element, index) => {
        const filename = element.closest('.card').querySelector('h5').textContent.trim();
        matches.push({
            filename: filename,
            text: element.innerText,
            index: index + 1
        });
    });
    
    return {
        query: query,
        timestamp: new Date().toISOString(),
        totalMatches: matches.length,
        matches: matches
    };
}

function exportAsText(data) {
    let content = `IR Legal Search Results\n`;
    content += `Query: ${data.query}\n`;
    content += `Search Date: ${new Date(data.timestamp).toLocaleString()}\n`;
    content += `Total Matches: ${data.totalMatches}\n`;
    content += `${'='.repeat(50)}\n\n`;
    
    data.matches.forEach((match, index) => {
        content += `Match ${index + 1}\n`;
        content += `File: ${match.filename}\n`;
        content += `Text: ${match.text}\n`;
        content += `${'-'.repeat(30)}\n\n`;
    });
    
    downloadFile(content, `search_results_${Date.now()}.txt`, 'text/plain');
}

function exportAsCSV(data) {
    let content = 'Index,Filename,Match Text\n';
    
    data.matches.forEach(match => {
        const escapedText = `"${match.text.replace(/"/g, '""')}"`;
        content += `${match.index},"${match.filename}",${escapedText}\n`;
    });
    
    downloadFile(content, `search_results_${Date.now()}.csv`, 'text/csv');
}

function exportAsHTML(data) {
    let content = `
<!DOCTYPE html>
<html>
<head>
    <title>Search Results - ${data.query}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .match { background: #ffffff; border: 1px solid #dee2e6; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .filename { font-weight: bold; color: #0d6efd; margin-bottom: 10px; }
        .text { line-height: 1.6; }
        .highlight { background-color: #fff3cd; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>IR Legal Search Results</h1>
        <p><strong>Query:</strong> ${data.query}</p>
        <p><strong>Search Date:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
        <p><strong>Total Matches:</strong> ${data.totalMatches}</p>
    </div>
`;
    
    data.matches.forEach((match, index) => {
        content += `
    <div class="match">
        <div class="filename">Match ${index + 1} - ${match.filename}</div>
        <div class="text">${match.text}</div>
    </div>`;
    });
    
    content += `
</body>
</html>`;
    
    downloadFile(content, `search_results_${Date.now()}.html`, 'text/html');
}

function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification(`Downloaded ${filename}`, 'success');
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Progress Bar Helper
function createProgressBar(filename) {
    const container = document.createElement('div');
    container.className = 'progress-container mt-3';
    container.innerHTML = `
        <div class="d-flex justify-content-between">
            <small>${filename}</small>
            <small>Uploading...</small>
        </div>
        <div class="progress">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 100%"></div>
        </div>
    `;
    
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.parentNode.appendChild(container);
    }
    
    return container;
}

// Search Suggestions (Basic Implementation)
function suggestQueries(input) {
    if (input.length < 3) return;
    
    // Basic suggestions based on common legal terms
    const suggestions = [
        '"contract law"',
        '"intellectual property"',
        '"data protection"',
        '"legal framework"',
        '"information system"',
        'liability AND damages',
        'copyright OR trademark',
        'privacy NOT commercial'
    ].filter(suggestion => 
        suggestion.toLowerCase().includes(input.toLowerCase())
    );
    
    // This could be enhanced to show actual suggestions in a dropdown
    console.log('Suggestions:', suggestions);
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+/ or Cmd+/ to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        const searchInput = document.getElementById('query');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('query');
        if (searchInput && searchInput === document.activeElement) {
            searchInput.value = '';
        }
    }
    
    // Ctrl+Enter to submit search
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.submit();
        }
    }
});

// Real-time Search (Optional - for future enhancement)
let searchTimeout;
function performRealtimeSearch(query) {
    clearTimeout(searchTimeout);
    
    if (query.length < 3) return;
    
    searchTimeout = setTimeout(() => {
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            // Update results without page reload
            updateResultsDisplay(data);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
    }, 500);
}

function updateResultsDisplay(results) {
    // This would update the results area without page reload
    // Implementation depends on your UI structure
    console.log('Real-time results:', results);
}

// File Management
function updateFileList() {
    fetch('/api/files')
        .then(response => response.json())
        .then(files => {
            const fileList = document.querySelector('.file-list');
            if (fileList) {
                fileList.innerHTML = '';
                files.forEach(file => {
                    const fileItem = document.createElement('li');
                    fileItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    fileItem.innerHTML = `
                        <span><i class="fas fa-file-pdf text-danger me-2"></i>${file.name}</span>
                        <small class="text-muted">${file.size}</small>
                    `;
                    fileList.appendChild(fileItem);
                });
            }
        })
        .catch(error => console.error('Error updating file list:', error));
}

// Search History Management
function saveSearchHistory(query, resultCount) {
    let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    
    const searchEntry = {
        query: query,
        resultCount: resultCount,
        timestamp: new Date().toISOString()
    };
    
    // Remove duplicate queries
    history = history.filter(entry => entry.query !== query);
    
    // Add new entry at the beginning
    history.unshift(searchEntry);
    
    // Keep only last 20 searches
    history = history.slice(0, 20);
    
    localStorage.setItem('searchHistory', JSON.stringify(history));
}

function loadSearchHistory() {
    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    const historyContainer = document.querySelector('.search-history');
    
    if (historyContainer && history.length > 0) {
        historyContainer.innerHTML = `
            <h6 class="text-muted mb-2">Recent Searches</h6>
            <div class="d-flex flex-wrap gap-2">
                ${history.slice(0, 5).map(entry => `
                    <button class="btn btn-outline-secondary btn-sm history-query" 
                            data-query="${entry.query}">
                        ${entry.query} <small class="text-muted">(${entry.resultCount})</small>
                    </button>
                `).join('')}
            </div>
        `;
        
        // Add click handlers for history items
        historyContainer.querySelectorAll('.history-query').forEach(button => {
            button.addEventListener('click', function() {
                const queryInput = document.getElementById('query');
                if (queryInput) {
                    queryInput.value = this.dataset.query;
                    queryInput.focus();
                }
            });
        });
    }
}

// Performance Monitoring
function trackSearchPerformance(startTime, resultCount) {
    const endTime = performance.now();
    const searchTime = endTime - startTime;
    
    console.log(`Search completed in ${searchTime.toFixed(2)}ms with ${resultCount} results`);
    
    // You could send this data to analytics
    // analytics.track('search_performance', {
    //     duration: searchTime,
    //     resultCount: resultCount
    // });
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    
    // Show user-friendly error message
    showNotification('An error occurred. Please try again.', 'error');
});

// Service Worker Registration (for offline support - future enhancement)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Analytics Integration (placeholder)
function trackEvent(category, action, label) {
    // Google Analytics or other analytics integration
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            event_category: category,
            event_label: label
        });
    }
    
    console.log('Event tracked:', category, action, label);
}

// Initialize search history on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSearchHistory();
});
