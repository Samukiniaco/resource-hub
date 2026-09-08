"""Modern theme — suporta dark/light/anime presets + custom via theme_service."""
import tkinter as tk
from tkinter import ttk

from app.services.theme_service import get_colors as _get_theme_colors, DEFAULT_DARK

# COLORS é mutável e reflete o tema atual (dark/light/custom)
COLORS = dict(_get_theme_colors())

FONTS = {
    "title": ("Segoe UI", 11, "bold"),
    "subtitle": ("Segoe UI", 10, "bold"),
    "body": ("Segoe UI", 9),
    "small": ("Segoe UI", 8),
    "small_bold": ("Segoe UI", 8, "bold"),
    "warning": ("Segoe UI", 8, "bold"),
    "mono": ("Consolas", 8),
    "brand": ("Segoe UI", 10, "bold"),
}

def reload_colors() -> None:
    """Recarrega COLORS do disco (theme.json) — útil após salvar tema."""
    from app.services.theme_service import get_colors
    new = get_colors()
    COLORS.clear()
    COLORS.update(new)

def apply_theme(root: tk.Tk, override: dict | None = None) -> None:
    # se override for passado (preview), mescla sobre COLORS sem persistir
    if override:
        # preview: não altera arquivo, só aplica visualmente
        preview = dict(COLORS)
        for k, v in override.items():
            if k in DEFAULT_DARK:
                preview[k] = v
        colors = preview
    else:
        reload_colors()
        colors = COLORS

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # frames
    style.configure("TFrame", background=colors["bg"])
    style.configure("Top.TFrame", background=colors["bg_top"])
    style.configure("Card.TFrame", background=colors["bg_card"], relief="flat")
    style.configure("CardInner.TFrame", background=colors["bg_card"])
    style.configure("Muted.TFrame", background=colors["bg"], relief="flat")

    # labels
    style.configure("TLabel", background=colors["bg"], foreground=colors["text_primary"], font=FONTS["body"])
    style.configure("Top.TLabel", background=colors["bg_top"], foreground=colors["text_primary"])
    style.configure("Muted.TLabel", background=colors["bg"], foreground=colors["text_muted"])
    style.configure("Card.TLabel", background=colors["bg_card"], foreground=colors["text_primary"])
    style.configure("CardSecondary.TLabel", background=colors["bg_card"], foreground=colors["text_secondary"])
    style.configure("CardMuted.TLabel", background=colors["bg_card"], foreground=colors["text_muted"])
    style.configure("Brand.TLabel", background=colors["bg_top"], foreground=colors["text_primary"], font=FONTS["brand"])
    style.configure("BrandSub.TLabel", background=colors["bg_top"], foreground=colors["text_muted"], font=FONTS["small"])
    style.configure("Header.TLabel", background=colors["bg"], foreground=colors["text_primary"], font=FONTS["title"])
    style.configure("Section.TLabel", background=colors["bg"], foreground=colors["text_muted"], font=FONTS["small_bold"])

    # notebook
    style.configure("TNotebook", background=colors["bg"], borderwidth=0, tabmargins=[6, 6, 6, 0])
    style.configure("TNotebook.Tab",
                    background=colors["bg_top"],
                    foreground=colors["text_muted"],
                    padding=[14, 8],
                    font=FONTS["small_bold"],
                    borderwidth=0,
                    focuscolor=colors["bg"])
    style.map("TNotebook.Tab",
              background=[("selected", colors["bg_card"]), ("active", colors["bg_card_hover"])],
              foreground=[("selected", colors["text_primary"]), ("active", colors["text_secondary"])],
              expand=[("selected", [1, 1, 1, 0])])

    # buttons
    style.configure("Accent.TButton",
                    background=colors["accent"],
                    foreground="white",
                    font=("Segoe UI", 9, "bold"),
                    padding=(14, 6),
                    borderwidth=0,
                    relief="flat")
    style.map("Accent.TButton",
              background=[("active", colors["accent_hover"]), ("pressed", colors["accent_press"]), ("disabled", colors["border"])],
              foreground=[("disabled", colors["text_dim"])])

    style.configure("Secondary.TButton",
                    background=colors["bg_top"],
                    foreground=colors["text_primary"],
                    font=("Segoe UI", 9),
                    padding=(14, 6),
                    borderwidth=1,
                    relief="flat",
                    bordercolor=colors["border"])
    style.map("Secondary.TButton",
              background=[("active", colors["border"]), ("pressed", colors["bg"])],
              bordercolor=[("active", colors["border_light"])],
              foreground=[("disabled", colors["text_dim"])])

    style.configure("Ghost.TButton",
                    background=colors["bg_top"],
                    foreground=colors["text_muted"],
                    font=FONTS["small"],
                    padding=(10, 4),
                    borderwidth=0)
    style.map("Ghost.TButton",
              foreground=[("active", colors["text_primary"])],
              background=[("active", colors["bg_card_hover"])])

    # scrollbar
    style.configure("Modern.Vertical.TScrollbar",
                    background=colors["bg"],
                    troughcolor=colors["scroll_trough"],
                    bordercolor=colors["bg"],
                    arrowcolor=colors["text_muted"],
                    relief="flat",
                    borderwidth=0,
                    arrowsize=0,
                    width=10)
    style.map("Modern.Vertical.TScrollbar",
              background=[("active", colors["scroll_thumb_hover"]), ("!active", colors["scroll_thumb"])],
              troughcolor=[("!active", colors["scroll_trough"])])

    style.configure("TSeparator", background=colors["border"])
    root.configure(bg=colors["bg"])
    try:
        root.option_add("*Font", FONTS["body"])
    except tk.TclError:
        pass
