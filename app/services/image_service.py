"""Async banner image fetching with disk cache and placeholder fallback."""
from __future__ import annotations

import hashlib
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable, Optional
import io

from app.config import IMAGE_CACHE_DIR, REQUEST_TIMEOUT
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None  # type: ignore
    ImageTk = None  # type: ignore

PLACEHOLDER_SIZE = (320, 160)
PLACEHOLDER_COLOR = (45, 45, 48)
PLACEHOLDER_TEXT_COLOR = (160, 160, 160)

# Cache for PhotoImage refs to avoid GC
_photo_cache: dict[str, object] = {}


def _url_to_cache_path(url: str) -> Path:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    # preserve extension if image-like
    ext = ".png"
    lower = url.lower()
    for e in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        if e in lower:
            ext = ".png" if e == ".webp" else e
            if ext == ".jpeg":
                ext = ".jpg"
            break
    return IMAGE_CACHE_DIR / f"{h}{ext}"


def ensure_placeholder_image() -> Optional[Path]:
    """Create placeholder.png in assets if missing, return path."""
    try:
        from pathlib import Path as P
        from app.config import ASSETS_DIR
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        ph = ASSETS_DIR / "placeholder.png"
        if ph.exists():
            return ph
        if not HAS_PIL:
            return None
        img = Image.new("RGB", PLACEHOLDER_SIZE, PLACEHOLDER_COLOR)
        # simple placeholder: no text to avoid font issues
        img.save(ph, format="PNG")
        return ph
    except Exception as e:
        logger.warning("Failed to create placeholder: %s", e)
        return None


def _load_image_from_path(path: Path, max_size: tuple[int, int]) -> Optional[object]:
    if not HAS_PIL:
        return None
    try:
        img = Image.open(path)
        img.load()
        # convert to RGB/RGBA as needed
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        # thumbnail
        img.thumbnail(max_size, Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        return tk_img
    except Exception as e:
        logger.debug("Failed to load image %s: %s", path, e)
        return None


def get_placeholder_tk(max_size: tuple[int, int] = (320, 160)) -> Optional[object]:
    if not HAS_PIL:
        return None
    key = f"__placeholder__{max_size}"
    if key in _photo_cache:
        return _photo_cache[key]
    ph_path = ensure_placeholder_image()
    if ph_path and ph_path.exists():
        img = _load_image_from_path(ph_path, max_size)
        if img:
            _photo_cache[key] = img
            return img
    # generate in-memory placeholder
    try:
        img = Image.new("RGB", max_size, PLACEHOLDER_COLOR)
        tk_img = ImageTk.PhotoImage(img)
        _photo_cache[key] = tk_img
        return tk_img
    except Exception:
        return None


def fetch_image_async(
    url: str,
    callback: Callable[[Optional[object]], None],
    max_size: tuple[int, int] = (320, 160),
) -> None:
    """Fetch image asynchronously, call callback(tk_image|None) on completion.

    Callback is invoked from background thread; caller must marshal to Tk thread via `after`.
    """
    if not url or not HAS_PIL:
        callback(get_placeholder_tk(max_size))
        return

    cache_path = _url_to_cache_path(url)

    # if cached on disk, load synchronously in thread but quickly
    def _work():
        # try disk cache first
        if cache_path.exists():
            tk_img = _load_image_from_path(cache_path, max_size)
            if tk_img:
                _photo_cache[url] = tk_img
                callback(tk_img)
                return
        # fetch remote
        try:
            IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "ResourceHub/1.0"})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    raise IOError(f"HTTP {resp.status}")
                data = resp.read()
                # write cache
                try:
                    cache_path.write_bytes(data)
                except OSError:
                    pass
                # load from bytes
                img = Image.open(io.BytesIO(data))
                img.load()
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                img.thumbnail(max_size, Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                _photo_cache[url] = tk_img
                callback(tk_img)
                return
        except Exception as e:
            logger.debug("Banner fetch failed %r: %s", url, e)
        # fallback
        callback(get_placeholder_tk(max_size))

    t = threading.Thread(target=_work, daemon=True, name="image-fetch")
    t.start()


def fetch_image_sync(url: str, max_size=(320, 160)) -> Optional[object]:
    """Sync version for tests or non-Tk contexts."""
    if not url or not HAS_PIL:
        return get_placeholder_tk(max_size)
    cache_path = _url_to_cache_path(url)
    if cache_path.exists():
        img = _load_image_from_path(cache_path, max_size)
        if img:
            return img
    return get_placeholder_tk(max_size)
