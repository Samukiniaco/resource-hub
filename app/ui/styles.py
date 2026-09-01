"""Modern lightweight theme for Tkinter."""
import tkinter as tk
from tkinter import ttk

COLORS = {
    "bg": "#1e1e1e",
    "bg_card": "#252526",
    "bg_card_hover": "#2d2d30",
    "accent": "#007acc",
    "accent_hover": "#1a8ad4",
    "text_primary": "#ffffff",
    "text_secondary": "#cccccc",
    "text_muted": "#969696",
    "warning_bg": "#3a2d00",
    "warning_fg": "#ffcc00",
    "border": "#3e3e42",
    "success": "#89d185",
    "error": "#f44747",
}

FONTS = {
    "title": ("Segoe UI", 11, "bold"),
    "subtitle": ("Segoe UI", 9),
    "body": ("Segoe UI", 9),
    "small": ("Segoe UI", 8),
    "warning": ("Segoe UI", 8, "bold"),
}

def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    # Use clam as base for custom colors
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=COLORS["bg"])
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text_primary"])
    style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background="#2d2d30", foreground=COLORS["text_secondary"], padding=[12, 6], font=FONTS["body"])
    style.map("TNotebook.Tab", background=[("selected", COLORS["bg_card"]), ("active", "#333333")],
              foreground=[("selected", COLORS["text_primary"])])

    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")
    style.configure("Card.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_primary"])
    style.configure("CardSecondary.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_secondary"])
    style.configure("CardMuted.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_muted"])

    style.configure("Accent.TButton", background=COLORS["accent"], foreground="white", font=FONTS["body"], padding=6)
    style.map("Accent.TButton", background=[("active", COLORS["accent_hover"]), ("pressed", "#005a9e")])

    style.configure("Secondary.TButton", background="#3a3a3a", foreground="white", font=FONTS["body"], padding=6)
    style.map("Secondary.TButton", background=[("active", "#4a4a4a")])

    # Scrollbar
    style.configure("Vertical.TScrollbar", background="#3e3e42")

    root.configure(bg=COLORS["bg"])
