#src/utils/logger.py

import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), '../../logs')
LOG_FILE = os.path.join(LOG_DIR, 'search_log.txt')

os.makedirs(LOG_DIR, exist_ok=True)


def log_search(keyword, results):
    """
    LOGS the search keyword and result details to a log file.
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
