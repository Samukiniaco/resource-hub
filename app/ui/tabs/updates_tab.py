import tkinter as tk
from tkinter import ttk, messagebox

from app.models.catalog import Catalog
from app.config import get_catalog_url
from app.ui.styles import COLORS, FONTS
from app.utils.browser import open_url

def build_updates_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=12)
    ttk.Label(frame, text="Atualizações / Sobre", style="TLabel", font=FONTS["title"]).pack(anchor="w", pady=(0, 8))

    if catalog:
        ttk.Label(frame, text=f"Versão do catálogo: {catalog.catalog_version}", style="TLabel", font=FONTS["subtitle"]).pack(anchor="w")
        if catalog.app.changelog:
            ttk.Label(frame, text="Changelog:", style="TLabel", font=FONTS["body"]).pack(anchor="w", pady=(12, 4))
            txt = tk.Text(frame, wrap="word", height=12, bg=COLORS["bg_card"], fg=COLORS["text_secondary"], relief="flat", padx=8, pady=8, font=FONTS["body"])
            txt.insert("1.0", catalog.app.changelog)
            txt.configure(state="disabled")
            txt.pack(fill="both", expand=True, pady=(0, 12))
        else:
            ttk.Label(frame, text="Sem notas de atualização.", style="TLabel", foreground=COLORS["text_muted"]).pack(anchor="w", pady=8)
    else:
        ttk.Label(frame, text="Catálogo não carregado.", style="TLabel", foreground=COLORS["error"]).pack(anchor="w")
        ttk.Label(frame, text="Verifique sua conexão e tente atualizar.", style="TLabel", foreground=COLORS["text_muted"]).pack(anchor="w", pady=4)

    # catalog URL section
    url_frame = ttk.Frame(frame, style="TFrame")
    url_frame.pack(fill="x", pady=8)
    url = get_catalog_url()
    ttk.Label(url_frame, text="URL do catálogo:", style="TLabel", font=FONTS["small"]).pack(anchor="w")
    ttk.Label(url_frame, text=url, style="TLabel", foreground=COLORS["accent"], font=FONTS["small"], wraplength=900).pack(anchor="w")
    def _open_cat():
        open_url(url)
    ttk.Button(url_frame, text="Abrir URL no navegador", style="Secondary.TButton", command=_open_cat).pack(anchor="w", pady=(6, 0))

    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=12)
    ttk.Label(frame, text="Resource Hub — utilitário leve para organizar recursos do launcher externo.\nNão baixa nem executa arquivos automaticamente. Apenas exibe informações e copia/abre links no navegador padrão.", style="TLabel", foreground=COLORS["text_muted"], font=FONTS["small"], justify="left").pack(anchor="w")
    ttk.Label(frame, text="Launcher externo não é modificado, embutido ou distribuído por este app.", style="TLabel", foreground=COLORS["text_muted"], font=FONTS["small"]).pack(anchor="w", pady=(4, 0))

    return frame
