import webbrowser
from urllib.parse import urlparse

from app.utils.logger import get_logger

logger = get_logger(__name__)

def is_valid_http_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        p = urlparse(url.strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def open_url(url: str) -> bool:
    """Open URL in default browser. Returns True on success."""
    if not is_valid_http_url(url):
        logger.warning("Refused to open invalid URL: %r", url)
        return False
    try:
        webbrowser.open(url.strip(), new=2)
        logger.info("Opened URL: %s", url)
        return True
    except Exception as e:
        logger.exception("Failed to open URL %r: %s", url, e)
        return False
