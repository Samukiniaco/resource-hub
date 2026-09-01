import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.styles import COLORS

def _scrollable(parent: tk.Misc):
    canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas, style="TFrame")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return scroll_frame

def build_other_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=8)
    inner = _scrollable(frame)
    if not catalog or not catalog.other:
        ttk.Label(inner, text="Nenhum patch ou arquivo adicional.", style="TLabel", foreground=COLORS["text_muted"]).pack(pady=40)
        return frame
    for o in catalog.other:
        title = f"{o.name}  [{o.category}]" if o.category and o.category != "other" else o.name
        card = ResourceCard(inner, title=title, description=o.description, link=o.link, banner_url=o.banner, warning=o.warning)
        card.pack(fill="x", pady=6, padx=6)
    return frame
