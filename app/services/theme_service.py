"""Tema local — presets anime light + persistência, import/export."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any

from app.config import DATA_DIR

THEME_PATH = DATA_DIR / "theme.json"
THEME_CUSTOM_HEADER = DATA_DIR / "header_bg.custom.png"

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Cores base (dark) — espelho de styles.COLORS
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

# Anime light — paletas suaves inspiradas nos animes citados
PRESETS: Dict[str, Dict[str, str]] = {
    "dark": DEFAULT_DARK,
    "light": LIGHT,
    "kobayashi": {  # Dragon Maid — verde suave + laranja Tohru
        **LIGHT, "accent": "#2e7d6f", "accent_hover": "#3a9a87", "accent_press": "#25665b", "accent_subtle": "#e0f2ef",
        "bg": "#fdf8f0", "bg_top": "#fffbf5", "border": "#f0e6d8",
    },
    "nichijou": {  # Nichijou — amarelo pastel + azul céu
        **LIGHT, "accent": "#f59e0b", "accent_hover": "#fbbf24", "accent_press": "#d97706", "accent_subtle": "#fef3c7",
        "bg": "#fffef5", "bg_top": "#ffffff", "border": "#fde68a",
    },
    "azumanga": {  # Azumanga — rosa sakura claro
        **LIGHT, "accent": "#ec4899", "accent_hover": "#f472b6", "accent_press": "#db2777", "accent_subtle": "#fce7f3",
        "bg": "#fff7f9", "bg_top": "#ffffff", "border": "#fbcfe8",
    },
    "k_on": {  # K-On — marrom chocolate + creme
        **LIGHT, "accent": "#b45309", "accent_hover": "#d97706", "accent_press": "#92400e", "accent_subtle": "#fef3c7",
        "bg": "#fdf6ec", "bg_top": "#fffaf0", "border": "#fde68a",
    },
    "bocchi": {  # Bocchi — roxo/azul escuro mas light
        **LIGHT, "accent": "#7c3aed", "accent_hover": "#8b5cf6", "accent_press": "#6d28d9", "accent_subtle": "#ede9fe",
        "bg": "#f8f7ff", "bg_top": "#ffffff", "border": "#ddd6fe",
    },
    "minecraft": {  # Minecraft — verde grama
        **DEFAULT_DARK, "accent": "#3B8526", "accent_hover": "#4a9c2d", "accent_press": "#2f6a1e", "accent_subtle": "#1e2e1a",
        "bg": "#1e221e", "bg_top": "#252a25", "border": "#3a3d2f",
    },
}

def _is_hex(s: str) -> bool:
    return isinstance(s, str) and bool(HEX_RE.match(s.strip()))

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
    # images: opcional, só guarda flag se existe custom header
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
    # custom overrides
    colors = dict(base)
    for k, v in info.get("colors", {}).items():
        if _is_hex(v):
            colors[k] = v.lower()
    return colors

def export_theme_file(path: Path) -> None:
    info = load_theme()
    # inclui cores atuais resolvidas
    colors = get_colors()
    payload = {
        "format": "rhtheme",
        "version": 1,
        "mode": info.get("mode", "custom"),
        "colors": colors,
        "meta": {"exported_from": "Resource Hub"}
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def import_theme_file(path: Path) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    # suporta rhtheme e theme.json direto
    colors = raw.get("colors") if "colors" in raw else raw
    if not isinstance(colors, dict):
        raise ValueError("Arquivo inválido: sem 'colors'")
    mode = raw.get("mode", "custom")
    # valida
    clean = {k: v for k, v in colors.items() if k in DEFAULT_DARK and _is_hex(str(v))}
    if not clean:
        raise ValueError("Nenhuma cor válida encontrada")
    save_theme(mode if mode in PRESETS or mode == "custom" else "custom", clean)
