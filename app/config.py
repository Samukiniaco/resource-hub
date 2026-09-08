"""Application-wide configuration.

Catalog URL is configurable via:
1) environment variable RESOURCE_HUB_CATALOG_URL
2) file data/catalog_url.txt (first line)
3) fallback constant DEFAULT_CATALOG_URL

Paths are resolved relative to project root (parent of app/).
Suporta PyInstaller frozen (sys.executable).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# --- Project paths ---
if getattr(sys, "frozen", False):
    # Compilado: exe em .../ResourceHub/, dados graváveis ao lado do exe
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    # assets podem estar dentro do bundle (_MEIPASS) no modo onefile
    _bundle = Path(getattr(sys, "_MEIPASS", str(PROJECT_ROOT)))
    _bundle_assets = _bundle / "assets"
    ASSETS_DIR = _bundle_assets if _bundle_assets.exists() else PROJECT_ROOT / "assets"
else:
    APP_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = APP_DIR.parent
    ASSETS_DIR = PROJECT_ROOT / "assets"

DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR

CATALOG_CACHE_PATH = CACHE_DIR / "catalog.json"
CATALOG_TMP_PATH = CACHE_DIR / "catalog.tmp.json"
CATALOG_URL_FILE = CACHE_DIR / "catalog_url.txt"
IMAGE_CACHE_DIR = CACHE_DIR / "image_cache"
VORTEX_CONF_NAME = "vortex_launcher.conf"
THEME_PATH = DATA_DIR / "theme.json"
THEME_CUSTOM_HEADER = DATA_DIR / "header_bg.custom.png"
HISTORY_CACHE_PATH = CACHE_DIR / "history_cache.json"
GITHUB_API_URL = "https://api.github.com/repos/Samukiniaco/resource-hub/commits"

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
