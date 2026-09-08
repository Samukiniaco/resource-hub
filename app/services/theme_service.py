"""Tema local — presets por cores/estilos + persistência, import/export."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any

from app.config import DATA_DIR

THEME_PATH = DATA_DIR / "theme.json"
THEME_CUSTOM_HEADER = DATA_DIR / "header_bg.custom.png"

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_DARK: Dict[str, str] = {
    "bg": "#121214",
    "bg_top": "#1a1a1d",
    "bg_card": "#1e1e22",
    "bg_card_hover": "#252529",
    "border": "#2a2a2e",
    "border_light": "#333338",
    "accent": "#2f80ed",
    "accent_hover": "#3b8bfa",
    "accent_press": "#1f6bd6",
    "accent_subtle": "#1c2333",
    "text_primary": "#f2f2f3",
    "text_secondary": "#b8b8bb",
    "text_muted": "#7c7c80",
    "text_dim": "#5e5e62",
    "warning_bg": "#2e2500",
    "warning_fg": "#ffd233",
    "warning_border": "#6b5200",
    "success": "#3fb950",
    "error": "#f85149",
    "scroll_trough": "#1a1a1d",
    "scroll_thumb": "#3a3a3f",
    "scroll_thumb_hover": "#4a4a50",
    "status_ok": "#3fb950",
    "status_warn": "#d29922",
    "status_err": "#f85149",
}

LIGHT: Dict[str, str] = {
    "bg": "#f5f5f7",
    "bg_top": "#ffffff",
    "bg_card": "#ffffff",
    "bg_card_hover": "#f0f0f2",
    "border": "#e5e5e7",
    "border_light": "#d4d4d8",
    "accent": "#2f80ed",
    "accent_hover": "#3b8bfa",
    "accent_press": "#1f6bd6",
    "accent_subtle": "#e8f0fe",
    "text_primary": "#18181b",
    "text_secondary": "#52525b",
    "text_muted": "#71717a",
    "text_dim": "#a1a1aa",
    "warning_bg": "#fef9c3",
    "warning_fg": "#854d0e",
    "warning_border": "#facc15",
    "success": "#16a34a",
    "error": "#dc2626",
    "scroll_trough": "#f5f5f7",
    "scroll_thumb": "#d4d4d8",
    "scroll_thumb_hover": "#a1a1aa",
    "status_ok": "#16a34a",
    "status_warn": "#ca8a04",
    "status_err": "#dc2626",
}

def _dark(accent: str, hover: str, press: str) -> Dict[str, str]:
    base = dict(DEFAULT_DARK)
    base.update({"accent": accent, "accent_hover": hover, "accent_press": press, "accent_subtle": "#1e2a3a"})
    return base

def _light(accent: str, hover: str, press: str, subtle: str, bg: str = "#f5f5f7", top: str = "#ffffff", border: str = "#e5e5e7") -> Dict[str, str]:
    base = dict(LIGHT)
    base.update({"accent": accent, "accent_hover": hover, "accent_press": press, "accent_subtle": subtle, "bg": bg, "bg_top": top, "border": border})
    return base

# Temas por cores/estilos (sem anime — combine com suas imagens)
PRESETS: Dict[str, Dict[str, str]] = {
    "dark": DEFAULT_DARK,
    "light": LIGHT,
    "sakura": _light("#e77a9a", "#ee98b0", "#d65f82", "#fde8ef", bg="#fff7f9", border="#fbcfe8"),
    "sakura_dark": _dark("#e77a9a", "#ee98b0", "#d65f82"),
    "ocean": _light("#2f80ed", "#3b8bfa", "#1f6bd6", "#e8f0fe"),
    "ocean_dark": _dark("#2f80ed", "#3b8bfa", "#1f6bd6"),
    "forest": _light("#2a9d8f", "#3ab09e", "#1f7a6e", "#dff5f0", bg="#fdf8f0", top="#fffbf5", border="#f0e6d8"),
    "forest_dark": _dark("#2a9d8f", "#3ab09e", "#1f7a6e"),
    "sunset": _light("#c47a1a", "#d98f2e", "#a8640f", "#fff3d6", bg="#fdf6ec", top="#fffaf0", border="#fde68a"),
    "sunset_dark": _dark("#c47a1a", "#d98f2e", "#a8640f"),
    "grape": _light("#6b7cff", "#8896ff", "#5566e0", "#ecefff", bg="#f8f7ff", border="#ddd6fe"),
    "grape_dark": _dark("#6b7cff", "#8896ff", "#5566e0"),
    "ember": _light("#f4b400", "#ffca28", "#e6a200", "#fff8d6", bg="#fffef5", border="#fde68a"),
    "ember_dark": _dark("#f4b400", "#ffca28", "#e6a200"),
    "minecraft": {**DEFAULT_DARK, "accent": "#3B8526", "accent_hover": "#4a9c2d", "accent_press": "#2f6a1e", "accent_subtle": "#1e2e1a", "bg": "#1e221e", "bg_top": "#252a25", "border": "#3a3d2f"},
    "minecraft_light": {**LIGHT, "accent": "#3B8526", "accent_hover": "#4a9c2d", "accent_press": "#2f6a1e", "accent_subtle": "#e8f5e3", "bg": "#f6fdf4", "bg_top": "#ffffff", "border": "#c5e0b8"},
}

def _is_hex(s: str) -> bool:
    return isinstance(s, str) and bool(HEX_RE.match(s.strip()))

def extract_dominant_color(image_path: Path) -> str | None:
    """Extrai cor dominante (região mais abundante) de uma imagem — para tema."""
    try:
        from PIL import Image
        im = Image.open(image_path).convert("RGB")
        im = im.resize((64, 64), Image.LANCZOS)
        im = im.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
        palette = im.getpalette()[:24]
        counts = im.getcolors(4096)
        if not counts:
            return None
        counts.sort(key=lambda x: x[0], reverse=True)
        idx = counts[0][1]
        r, g, b = palette[idx*3:idx*3+3]
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None

def validate_theme_dict(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Tema deve ser objeto JSON")
    out: Dict[str, Any] = {}
    mode = str(data.get("mode", "custom")).strip().lower()
    if mode not in PRESETS and mode != "custom":
        mode = "custom"
    out["mode"] = mode
    colors = data.get("colors", {})
    if not isinstance(colors, dict):
        colors = {}
    clean: Dict[str, str] = {}
    for k, v in colors.items():
        if k in DEFAULT_DARK and isinstance(v, str) and _is_hex(v.strip()):
            clean[k] = v.strip().lower()
    out["colors"] = clean
    if THEME_CUSTOM_HEADER.exists():
        out["has_custom_header"] = True
    return out

def load_theme() -> Dict[str, Any]:
    if not THEME_PATH.exists():
        return {"mode": "dark", "colors": {}}
    try:
        raw = json.loads(THEME_PATH.read_text(encoding="utf-8"))
        return validate_theme_dict(raw)
    except Exception:
        return {"mode": "dark", "colors": {}}

def save_theme(mode: str, colors: Dict[str, str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {"mode": mode, "colors": {k: v for k, v in colors.items() if k in DEFAULT_DARK and _is_hex(v)}}
    THEME_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def reset_theme() -> None:
    try:
        THEME_PATH.unlink(missing_ok=True)
    except OSError:
        pass
    try:
        THEME_CUSTOM_HEADER.unlink(missing_ok=True)
    except OSError:
        pass

def get_colors() -> Dict[str, str]:
    info = load_theme()
    mode = info.get("mode", "dark")
    base = PRESETS.get(mode, DEFAULT_DARK) if mode in PRESETS else DEFAULT_DARK
    colors = dict(base)
    for k, v in info.get("colors", {}).items():
        if _is_hex(v):
            colors[k] = v.lower()
    return colors

def export_theme_file(path: Path) -> None:
    info = load_theme()
    colors = get_colors()
    # banner settings + carrossel (o .rhtheme agora leva tudo)
    try:
        from app.services.image_service import get_banner_settings as _gbs
        banner = _gbs()
    except Exception:
        banner = {"fit": "blur", "focal": "top", "height": 200}
    try:
        from app.services.banner_carousel import load_carousel as _lc
        carousel = _lc()
    except Exception:
        carousel = []
    payload = {
        "format": "rhtheme",
        "version": 2,
        "mode": info.get("mode", "custom"),
        "colors": colors,
        "banner_fit": banner.get("fit", "blur"),
        "banner_focal": banner.get("focal", "top"),
        "banner_height": int(banner.get("height", 200)),
        "carousel": carousel,
        "meta": {"exported_from": "Resource Hub"}
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def import_theme_file(path: Path) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    colors = raw.get("colors") if "colors" in raw else raw
    if not isinstance(colors, dict):
        raise ValueError("Arquivo inválido: sem 'colors'")
    mode = raw.get("mode", "custom")
    clean = {k: v for k, v in colors.items() if k in DEFAULT_DARK and _is_hex(str(v))}
    if not clean and mode not in PRESETS:
        raise ValueError("Nenhuma cor válida encontrada")
    save_theme(mode if mode in PRESETS or mode == "custom" else "custom", clean or colors)
    # banner settings (v2)
    try:
        import json as _js
        from app.config import DATA_DIR as _DD
        _tp = _DD / "theme.json"
        _cur = _js.loads(_tp.read_text(encoding="utf-8")) if _tp.exists() else {}
        for k in ("banner_fit", "banner_focal", "banner_height"):
            if k in raw:
                _cur[k] = raw[k]
        _tp.write_text(_js.dumps(_cur, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass
    # carrossel (v2) — restaura imagens perdidas
    try:
        car = raw.get("carousel", [])
        if isinstance(car, list) and car:
            from app.services.banner_carousel import save_carousel as _sc
            _sc([str(u) for u in car if isinstance(u, str) and u.startswith("http")])
    except Exception:
        pass
