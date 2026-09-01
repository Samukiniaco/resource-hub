"""Reusable resource card: name, description, banner, warning, Open/Copy buttons."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from app.ui.styles import COLORS, FONTS
from app.utils.browser import open_url, is_valid_http_url
from app.utils.clipboard import copy_to_clipboard
from app.services.image_service import fetch_image_async
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ResourceCard(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        description: str = "",
        link: str = "",
        banner_url: str = "",
        warning: str = "",
        **kwargs,
    ):
        super().__init__(parent, style="Card.TFrame", padding=12, **kwargs)
        self.link = link.strip() if link else ""
        self.banner_url = banner_url.strip() if banner_url else ""

        # border effect via frame
        self.configure(relief="flat", borderwidth=1)

        # Layout: left content, right buttons? Use grid
        self.columnconfigure(0, weight=1)

        # Title
        ttk.Label(self, text=title, style="Card.TLabel", font=FONTS["title"], wraplength=680, justify="left").grid(row=0, column=0, sticky="w", pady=(0, 4))

        # Description
        if description:
            ttk.Label(self, text=description, style="CardSecondary.TLabel", font=FONTS["body"], wraplength=680, justify="left").grid(row=1, column=0, sticky="w", pady=(0, 6))
        else:
            ttk.Label(self, text="Sem descrição.", style="CardMuted.TLabel", font=FONTS["small"]).grid(row=1, column=0, sticky="w", pady=(0, 6))

        # Banner (async)
        self.banner_label = ttk.Label(self, style="Card.TLabel", text="", anchor="center")
        self.banner_label.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        if self.banner_url:
            self.banner_label.configure(text="Carregando banner...", font=FONTS["small"], foreground=COLORS["text_muted"])
            self._load_banner(self.banner_url)
        else:
            # no banner: hide label
            self.banner_label.grid_remove()

        # Warning
        if warning:
            warn_frame = tk.Frame(self, bg=COLORS["warning_bg"], highlightthickness=0)
            warn_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
            tk.Label(warn_frame, text=f"⚠ {warning}", bg=COLORS["warning_bg"], fg=COLORS["warning_fg"], font=FONTS["warning"], wraplength=660, justify="left", padx=8, pady=6).pack(fill="x")

        # Buttons row
        btn_frame = ttk.Frame(self, style="Card.TFrame")
        btn_frame.grid(row=4, column=0, sticky="ew", pady=(4, 0))
        btn_frame.columnconfigure(0, weight=1)

        self.open_btn = ttk.Button(btn_frame, text="Abrir", style="Accent.TButton", command=self._on_open, width=12)
        self.open_btn.pack(side="left", padx=(0, 8))
        self.copy_btn = ttk.Button(btn_frame, text="Copiar Link", style="Secondary.TButton", command=self._on_copy, width=12)
        self.copy_btn.pack(side="left")

        # Link preview (muted, single line)
        if self.link:
            preview = self.link if len(self.link) < 80 else self.link[:77] + "..."
            ttk.Label(btn_frame, text=preview, style="CardMuted.TLabel", font=FONTS["small"]).pack(side="left", padx=(12, 0))
        else:
            self.open_btn.configure(state="disabled")
            self.copy_btn.configure(state="disabled")
            ttk.Label(btn_frame, text="Sem link disponível", style="CardMuted.TLabel", font=FONTS["small"]).pack(side="left", padx=(12, 0))

        # hover effect
        self.bind("<Enter>", lambda e: self.configure(style="Card.TFrame"))
        # Use tk frame bg change for hover? Keep simple.

    def _load_banner(self, url: str):
        def _cb(tk_img):
            # must run on Tk thread
            def _apply():
                try:
                    if tk_img is not None:
                        self.banner_label.configure(image=tk_img, text="")
                        self.banner_label.image = tk_img  # keep ref
                    else:
                        self.banner_label.configure(text="Banner indisponível", image="")
                except tk.TclError:
                    pass
            # schedule on main thread
            try:
                self.after(0, _apply)
            except tk.TclError:
                pass

        fetch_image_async(url, _cb, max_size=(640, 160))

    def _on_open(self):
        if not self.link:
            messagebox.showinfo("Sem link", "Este recurso não possui link.", parent=self)
            return
        if not is_valid_http_url(self.link):
            messagebox.showerror("Link inválido", f"URL inválida:\n{self.link}", parent=self)
            return
        ok = open_url(self.link)
        if not ok:
            messagebox.showerror("Erro", f"Não foi possível abrir:\n{self.link}", parent=self)

    def _on_copy(self):
        if not self.link:
            return
        ok = copy_to_clipboard(self.winfo_toplevel(), self.link)
        if ok:
            # brief feedback
            orig = self.copy_btn.cget("text")
            self.copy_btn.configure(text="Copiado!")
            self.after(1500, lambda: self.copy_btn.configure(text=orig))
        else:
            messagebox.showerror("Erro", "Falha ao copiar para a área de transferência.", parent=self)
