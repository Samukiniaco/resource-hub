"""Card polido — bordas suaves, banner, hover, sem glitch visual."""
import tkinter as tk
from tkinter import ttk, messagebox

from app.ui.styles import COLORS, FONTS
from app.utils.browser import open_url, is_valid_http_url
from app.utils.clipboard import copy_to_clipboard
from app.services.image_service import fetch_image_async
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ResourceCard(tk.Frame):
    def __init__(self, parent, title: str, description: str = "", link: str = "", banner_url: str = "", warning: str = "", **kwargs):
        super().__init__(parent, bg=COLORS["border"], bd=0, highlightthickness=0, **kwargs)
        self.link = link.strip() if link else ""
        self.banner_url = banner_url.strip() if banner_url else ""

        # inner card fills outer with 1px border effect
        self.card = tk.Frame(self, bg=COLORS["bg_card"], bd=0, highlightthickness=0)
        self.card.pack(fill="both", expand=True, padx=1, pady=1)
        self.card.columnconfigure(0, weight=1)

        # header: dot + title
        header = tk.Frame(self.card, bg=COLORS["bg_card"])
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        dot_color = COLORS["accent"] if self.link and is_valid_http_url(self.link) else COLORS["border_light"]
        tk.Label(header, text="●", fg=dot_color, bg=COLORS["bg_card"], font=("Segoe UI", 7)).pack(side="left", padx=(0, 8))
        tk.Label(header, text=title, bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=FONTS["title"],
                 wraplength=620, justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        # description
        if description:
            tk.Label(self.card, text=description, bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                     font=FONTS["body"], wraplength=620, justify="left", anchor="w").grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))
        else:
            tk.Label(self.card, text="Sem descrição.", bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                     font=FONTS["small"]).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))

        # banner
        self.banner_label = tk.Label(self.card, bg=COLORS["bg_card"], bd=0, highlightthickness=0)
        self.banner_label.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        if self.banner_url:
            self.banner_label.configure(text="  Carregando banner…", fg=COLORS["text_muted"], font=FONTS["small"], anchor="w")
            self._load_banner(self.banner_url)
        else:
            self.banner_label.grid_remove()

        # warning
        if warning:
            wf = tk.Frame(self.card, bg=COLORS["warning_bg"], highlightbackground=COLORS["warning_border"], highlightthickness=1, bd=0)
            wf.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
            inner = tk.Frame(wf, bg=COLORS["warning_bg"])
            inner.pack(fill="x", padx=8, pady=6)
            tk.Label(inner, text="⚠  " + warning, bg=COLORS["warning_bg"], fg=COLORS["warning_fg"],
                     font=FONTS["warning"], wraplength=560, justify="left", anchor="w").pack(fill="x")

        # separator
        sep = tk.Frame(self.card, bg=COLORS["border"], height=1, bd=0, highlightthickness=0)
        sep.grid(row=4, column=0, sticky="ew", padx=14, pady=(2, 10))

        # buttons row
        btn_frame = tk.Frame(self.card, bg=COLORS["bg_card"])
        btn_frame.grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 12))
        left = tk.Frame(btn_frame, bg=COLORS["bg_card"])
        left.pack(side="left")
        right = tk.Frame(btn_frame, bg=COLORS["bg_card"])
        right.pack(side="right", fill="x", expand=True)
        # to have ttk buttons styled, need ttk parent with correct bg; use ttk.Frame inside tk.Frame
        btn_box = ttk.Frame(left, style="Card.TFrame")
        btn_box.pack(anchor="w")
        self.open_btn = ttk.Button(btn_box, text=" Abrir ↗ ", style="Accent.TButton", command=self._on_open, width=11)
        self.open_btn.pack(side="left", padx=(0, 8))
        self.copy_btn = ttk.Button(btn_box, text="Copiar link", style="Secondary.TButton", command=self._on_copy, width=11)
        self.copy_btn.pack(side="left")
        if not self.link:
            self.open_btn.configure(state="disabled")
            self.copy_btn.configure(state="disabled")
        # link preview
        if self.link:
            preview = self.link if len(self.link) <= 52 else self.link[:49] + "…"
            tk.Label(right, text=preview, bg=COLORS["bg_card"], fg=COLORS["text_dim"], font=FONTS["mono"], anchor="e").pack(anchor="e", padx=(12, 0))
        else:
            tk.Label(right, text="sem link", bg=COLORS["bg_card"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="e")

        # hover
        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.card.bind("<Enter>", self._on_enter, add="+")
        self.card.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, e):
        self.configure(bg=COLORS["border_light"])
        self.card.configure(bg=COLORS["bg_card_hover"])

    def _on_leave(self, e):
        self.configure(bg=COLORS["border"])
        self.card.configure(bg=COLORS["bg_card"])

    def _load_banner(self, url: str):
        def _cb(tk_img):
            def _apply():
                try:
                    if tk_img is not None:
                        self.banner_label.configure(image=tk_img, text="", compound="center")
                        self.banner_label.image = tk_img
                    else:
                        self.banner_label.configure(text="Banner indisponível", image="", fg=COLORS["text_muted"], font=FONTS["small"])
                except tk.TclError:
                    pass
            try:
                self.after(0, _apply)
            except tk.TclError:
                pass
        fetch_image_async(url, _cb, max_size=(620, 170))

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
            orig = self.copy_btn.cget("text")
            self.copy_btn.configure(text="✓ Copiado!")
            self.after(1400, lambda: self.copy_btn.configure(text=orig))
        else:
            messagebox.showerror("Erro", "Falha ao copiar.", parent=self)
