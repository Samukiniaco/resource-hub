import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.components.scrollable import ScrollableFrame
from app.ui.styles import COLORS, FONTS

def build_other_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=0)
    header = ttk.Frame(frame, style="TFrame", padding=(12, 10, 12, 6))
    header.pack(fill="x")
    ttk.Label(header, text="Patches & extras", style="Section.TLabel").pack(side="left")
    count = len(catalog.other) if catalog and catalog.other else 0
    ttk.Label(header, text=f"{count} itens", style="Muted.TLabel", font=FONTS["small"]).pack(side="right")

    sc = ScrollableFrame(frame)
    sc.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    inner = sc.inner

    if not catalog or not catalog.other:
        empty = ttk.Frame(inner, style="Card.TFrame", padding=20)
        empty.pack(fill="x", padx=12, pady=24)
        ttk.Label(empty, text="Nenhum patch ou arquivo adicional.", style="Card.TLabel", font=FONTS["subtitle"]).pack()
        ttk.Label(empty, text="Adicione entradas em 'other' no catálogo para aparecerem aqui.", style="CardMuted.TLabel", font=FONTS["small"]).pack(pady=(4, 0))
        return frame

    for o in catalog.other:
        title = f"{o.name}  ·  {o.category}" if o.category and o.category != "other" else o.name
        card = ResourceCard(inner, title=title, description=o.description, link=o.link, banner_url=o.banner, warning=o.warning)
        card.pack(fill="x", padx=12, pady=6)
    ttk.Frame(inner, style="TFrame", height=8).pack(fill="x")
    return frame
