import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.components.scrollable import ScrollableFrame
from app.ui.styles import COLORS, FONTS

def build_libraries_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=0)
    header = ttk.Frame(frame, style="TFrame", padding=(12, 10, 12, 6))
    header.pack(fill="x")
    ttk.Label(header, text="Pacote global", style="Section.TLabel").pack(side="left")
    ttk.Label(header, text="instalação única", style="Muted.TLabel", font=FONTS["small"]).pack(side="right")

    sc = ScrollableFrame(frame)
    sc.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    inner = sc.inner

    if not catalog or not catalog.libraries:
        empty = ttk.Frame(inner, style="Card.TFrame", padding=20)
        empty.pack(fill="x", padx=12, pady=24)
        ttk.Label(empty, text="Nenhuma biblioteca configurada.", style="Card.TLabel", font=FONTS["subtitle"]).pack()
        ttk.Label(empty, text="O catálogo remoto ainda não definiu o pacote global.", style="CardMuted.TLabel", font=FONTS["small"]).pack(pady=(4, 0))
        return frame

    libs = catalog.libraries
    name = libs.get("name") or libs.get("title") or "Bibliotecas Compartilhadas"
    description = libs.get("description") or libs.get("desc") or "Pacote global compartilhado entre todas as versões. Instale uma única vez."
    link = libs.get("link") or libs.get("url") or ""
    banner = libs.get("banner") or ""
    warning = libs.get("warning") or ""

    card = ResourceCard(inner, title=str(name), description=str(description), link=str(link), banner_url=str(banner), warning=str(warning))
    card.pack(fill="x", padx=12, pady=6)

    extra = {k: v for k, v in libs.items() if k not in ("name", "title", "description", "desc", "link", "url", "banner", "warning")}
    if extra:
        detail = tk.Frame(inner, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
        detail.pack(fill="x", padx=12, pady=6)
        inner2 = tk.Frame(detail, bg=COLORS["bg_card"])
        inner2.pack(fill="x", padx=14, pady=12)
        tk.Label(inner2, text="Detalhes adicionais", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small_bold"]).pack(anchor="w", pady=(0, 6))
        for k, v in extra.items():
            tk.Label(inner2, text=f"{k}: {v}", bg=COLORS["bg_card"], fg=COLORS["text_secondary"], font=FONTS["small"], wraplength=580, justify="left", anchor="w").pack(anchor="w", pady=1)

    ttk.Frame(inner, style="TFrame", height=8).pack(fill="x")
    return frame
