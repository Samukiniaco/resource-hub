"""Modern dark theme — polido, leve e não-editor."""
import tkinter as tk
from tkinter import ttk

COLORS = {
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

def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # frames
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Top.TFrame", background=COLORS["bg_top"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")
    style.configure("CardInner.TFrame", background=COLORS["bg_card"])
    style.configure("Muted.TFrame", background=COLORS["bg"], relief="flat")

    # labels
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text_primary"], font=FONTS["body"])
    style.configure("Top.TLabel", background=COLORS["bg_top"], foreground=COLORS["text_primary"])
    style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["text_muted"])
    style.configure("Card.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_primary"])
    style.configure("CardSecondary.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_secondary"])
    style.configure("CardMuted.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_muted"])
    style.configure("Brand.TLabel", background=COLORS["bg_top"], foreground=COLORS["text_primary"], font=FONTS["brand"])
    style.configure("BrandSub.TLabel", background=COLORS["bg_top"], foreground=COLORS["text_muted"], font=FONTS["small"])
    style.configure("Header.TLabel", background=COLORS["bg"], foreground=COLORS["text_primary"], font=FONTS["title"])
    style.configure("Section.TLabel", background=COLORS["bg"], foreground=COLORS["text_muted"], font=FONTS["small_bold"])

    # notebook — abas maiores, borda arredondada visual
    style.configure("TNotebook", background=COLORS["bg"], borderwidth=0, tabmargins=[6, 6, 6, 0])
    style.configure("TNotebook.Tab",
                    background=COLORS["bg_top"],
                    foreground=COLORS["text_muted"],
                    padding=[14, 8],
                    font=FONTS["small_bold"],
                    borderwidth=0,
                    focuscolor=COLORS["bg"])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["bg_card"]), ("active", "#222226")],
              foreground=[("selected", COLORS["text_primary"]), ("active", COLORS["text_secondary"])],
              expand=[("selected", [1, 1, 1, 0])])

    # buttons
    style.configure("Accent.TButton",
                    background=COLORS["accent"],
                    foreground="white",
                    font=("Segoe UI", 9, "bold"),
                    padding=(14, 6),
                    borderwidth=0,
                    relief="flat")
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent_press"]), ("disabled", "#2a2a2e")],
              foreground=[("disabled", COLORS["text_dim"])])

    style.configure("Secondary.TButton",
                    background="#232326",
                    foreground=COLORS["text_primary"],
                    font=("Segoe UI", 9),
                    padding=(14, 6),
                    borderwidth=1,
                    relief="flat",
                    bordercolor=COLORS["border"])
    style.map("Secondary.TButton",
              background=[("active", "#2a2a2e"), ("pressed", "#1e1e22")],
              bordercolor=[("active", COLORS["border_light"])],
              foreground=[("disabled", COLORS["text_dim"])])

    style.configure("Ghost.TButton",
                    background=COLORS["bg_top"],
                    foreground=COLORS["text_muted"],
                    font=FONTS["small"],
                    padding=(10, 4),
                    borderwidth=0)
    style.map("Ghost.TButton",
              foreground=[("active", COLORS["text_primary"])],
              background=[("active", "#252529")])

    # scrollbar moderna — visível, não decorativa
    style.configure("Modern.Vertical.TScrollbar",
                    background=COLORS["bg"],
                    troughcolor=COLORS["scroll_trough"],
                    bordercolor=COLORS["bg"],
                    arrowcolor=COLORS["text_muted"],
                    relief="flat",
                    borderwidth=0,
                    arrowsize=0,
                    width=10)
    style.map("Modern.Vertical.TScrollbar",
              background=[("active", COLORS["scroll_thumb_hover"]), ("!active", COLORS["scroll_thumb"])],
              troughcolor=[("!active", COLORS["scroll_trough"])])

    # separator
    style.configure("TSeparator", background=COLORS["border"])

    root.configure(bg=COLORS["bg"])
    # melhora renderização de fontes no Windows
    try:
        root.option_add("*Font", FONTS["body"])
    except tk.TclError:
        pass
