import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.config import get_catalog_url
from app.ui.styles import COLORS, FONTS
from app.utils.browser import open_url
from app.ui.components.scrollable import ScrollableFrame

def build_updates_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=0)
    sc = ScrollableFrame(frame)
    sc.pack(fill="both", expand=True, padx=8, pady=8)
    inner = sc.inner

    # header hero
    hero = tk.Frame(inner, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    hero.pack(fill="x", padx=12, pady=12)
    h = tk.Frame(hero, bg=COLORS["bg_card"])
    h.pack(fill="x", padx=16, pady=14)
    tk.Label(h, text="Resource Hub", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=("Segoe UI", 13, "bold")).pack(anchor="w")
    tk.Label(h, text="Atualizações  ·  Sobre", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small_bold"]).pack(anchor="w", pady=(2, 0))
    tk.Label(h, text="O catálogo remoto é a única fonte da verdade. O app nunca baixa ou executa arquivos — apenas abre links no navegador.",
             bg=COLORS["bg_card"], fg=COLORS["text_secondary"], font=FONTS["small"], wraplength=640, justify="left").pack(anchor="w", pady=(8, 0))

    # versão
    card = tk.Frame(inner, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    card.pack(fill="x", padx=12, pady=6)
    c = tk.Frame(card, bg=COLORS["bg_card"])
    c.pack(fill="x", padx=16, pady=12)
    if catalog:
        tk.Label(c, text=f"Versão do catálogo:  {catalog.catalog_version}", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=FONTS["subtitle"]).pack(anchor="w")
        tk.Label(c, text=f"Schema v{catalog.schema_version}  ·  {len(catalog.minecraft_versions)} Minecraft  ·  {len(catalog.java)} Java  ·  {len(catalog.other)} outros",
                 bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(anchor="w", pady=(4, 10))
        if catalog.app.changelog:
            tk.Label(c, text="Changelog", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small_bold"]).pack(anchor="w")
            txt = tk.Text(c, wrap="word", height=10, bg=COLORS["bg"], fg=COLORS["text_secondary"], relief="flat", bd=0,
                          padx=10, pady=10, font=FONTS["body"], highlightthickness=1, highlightbackground=COLORS["border"])
            txt.insert("1.0", catalog.app.changelog)
            txt.configure(state="disabled")
            txt.pack(fill="both", expand=True, pady=(6, 0))
        else:
            tk.Label(c, text="Sem notas de atualização.", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(anchor="w", pady=8)
    else:
        tk.Label(c, text="Catálogo não carregado.", bg=COLORS["bg_card"], fg=COLORS["error"], font=FONTS["subtitle"]).pack(anchor="w")
        tk.Label(c, text="Verifique a conexão e tente atualizar.", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(anchor="w", pady=4)

    # URL
    url_frame = tk.Frame(inner, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    url_frame.pack(fill="x", padx=12, pady=6)
    u = tk.Frame(url_frame, bg=COLORS["bg_card"])
    u.pack(fill="x", padx=16, pady=12)
    tk.Label(u, text="URL do catálogo", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small_bold"]).pack(anchor="w")
    url = get_catalog_url()
    lbl = tk.Label(u, text=url, bg=COLORS["bg_card"], fg=COLORS["accent"], font=FONTS["mono"], wraplength=580, justify="left", anchor="w", cursor="hand2")
    lbl.pack(anchor="w", pady=(4, 8), fill="x")
    lbl.bind("<Button-1>", lambda e: open_url(url))
    btn_row = ttk.Frame(u, style="Card.TFrame")
    btn_row.pack(anchor="w")
    ttk.Button(btn_row, text="Abrir URL no navegador", style="Secondary.TButton", command=lambda: open_url(url)).pack(side="left")

    # footer
    ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=12, pady=12)
    tk.Label(inner, text="Launcher externo não é modificado, embutido ou distribuído por este app.",
             bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="w", padx=16, pady=(0, 2))
    tk.Label(inner, text="© Resource Hub — utilitário leve, sem rastreamento, sem execução automática.",
             bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="w", padx=16, pady=(0, 12))

    return frame
