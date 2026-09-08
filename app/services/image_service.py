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


# --- Banners automáticos ---
def _banner_cache_key(title: str, max_size: tuple[int, int]) -> str:
    import hashlib
    h = hashlib.sha256(title.encode("utf-8")).hexdigest()[:8]
    return f"__auto_banner__{h}_{max_size[0]}x{max_size[1]}"

def get_anime_image_url(title: str, w: int = 620, h: int = 170) -> str:
    """URL determinística puxada da internet — sem API key, cacheável."""
    import hashlib
    # hash estável por título → seed para picsum (foto real) + waifu fallback
    seed = hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]
    # picsum.photos é confiável, 200ms, sem CORS, sempre retorna imagem
    # para variar: usa seed, garante mesma imagem por título
    return f"https://picsum.photos/seed/{seed}/{w}/{h}"

def get_auto_banner_tk(title: str, max_size: tuple[int, int] = (620, 170)) -> Optional[object]:
    """Gera banner procedural bonito (fallback se rede falhar) — anime-light / minecraft."""
    if not HAS_PIL:
        return get_placeholder_tk(max_size)
    key = _banner_cache_key(title, max_size)
    if key in _photo_cache:
        return _photo_cache[key]
    try:
        from app.services.theme_service import get_colors
        colors = get_colors()
        bg = colors.get("bg_card", "#1e1e22")
        accent = colors.get("accent", "#2f80ed")
        text_col = colors.get("text_primary", "#f2f2f3")
        muted = colors.get("text_muted", "#7c7c80")

        def _hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        w, h = max_size
        img = Image.new("RGB", (w, h), _hex_to_rgb(bg))
        draw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).ImageDraw.Draw(img)
        try:
            ar, ag, ab = _hex_to_rgb(accent)
            for y in range(4):
                draw.line((0, y, w, y), fill=(ar, ag, ab))
        except Exception:
            pass
        short = title[:42] + ("…" if len(title) > 42 else "")
        try:
            from PIL import ImageFont
            try:
                font_title = ImageFont.truetype("segoeui.ttf", 16)
                font_sub = ImageFont.truetype("segoeui.ttf", 9)
            except Exception:
                font_title = ImageFont.load_default()
                font_sub = ImageFont.load_default()
        except Exception:
            font_title = None
            font_sub = None

        pad = 12
        box_y0 = h//2 - 22
        box_y1 = h//2 + 22
        draw.rounded_rectangle((pad, box_y0, w-pad, box_y1), radius=10, fill=(35,35,39) if bg.startswith("#1") else (245,245,247), outline=_hex_to_rgb(colors.get("border", "#2a2a2e")), width=1)
        draw.text((w/2, h/2 - 6), short, fill=_hex_to_rgb(text_col), font=font_title, anchor="mm")
        draw.text((w/2, h/2 + 12), "Resource Hub  •  banner automático", fill=_hex_to_rgb(muted), font=font_sub, anchor="mm")
        draw.ellipse((w-28, h-28, w-12, h-12), fill=_hex_to_rgb(accent), outline=None)
        draw.text((w-20, h-20), "⛏", fill=(255,255,255), font=font_sub, anchor="mm")

        img.thumbnail(max_size, Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        _photo_cache[key] = tk_img
        return tk_img
    except Exception as e:
        logger.debug("auto banner failed %r: %s", title, e)
        return get_placeholder_tk(max_size)
