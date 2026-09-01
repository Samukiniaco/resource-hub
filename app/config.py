"""Application-wide configuration.

Catalog URL is configurable via:
1) environment variable RESOURCE_HUB_CATALOG_URL
2) file data/catalog_url.txt (first line)
3) fallback constant DEFAULT_CATALOG_URL

Paths are resolved relative to project root (parent of app/).
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Project paths ---
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
CACHE_DIR = DATA_DIR

CATALOG_CACHE_PATH = CACHE_DIR / "catalog.json"
CATALOG_TMP_PATH = CACHE_DIR / "catalog.tmp.json"
CATALOG_URL_FILE = CACHE_DIR / "catalog_url.txt"
IMAGE_CACHE_DIR = CACHE_DIR / "image_cache"
VORTEX_CONF_NAME = "vortex_launcher.conf"

# --- Remote catalog ---
DEFAULT_CATALOG_URL = "https://raw.githubusercontent.com/Samukiniaco/resource-hub/master/data/catalog.json"
SCHEMA_VERSION = 1
REQUEST_TIMEOUT = 10  # seconds

# --- UI ---
APP_TITLE = "Resource Hub"
APP_GEOMETRY = "1020x680"

def get_catalog_url() -> str:
    """Return configurable catalog URL."""
    env_url = os.environ.get("RESOURCE_HUB_CATALOG_URL", "").strip()
    if env_url:
        return env_url
    if CATALOG_URL_FILE.exists():
        try:
            text = CATALOG_URL_FILE.read_text(encoding="utf-8").strip()
            if text:
                return text.splitlines()[0].strip()
        except OSError:
            pass
    return DEFAULT_CATALOG_URL

def set_catalog_url(url: str) -> None:
    """Persist catalog URL to data/catalog_url.txt."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_URL_FILE.write_text(url.strip() + "\n", encoding="utf-8")
