import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.styles import COLORS

def _scrollable(parent: tk.Misc) -> tuple[ttk.Frame, tk.Canvas]:
    canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas, style="TFrame")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    def _on_config(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scroll_frame.bind("<Configure>", _on_config)
    # mousewheel
    def _on_wheel(e):
        canvas.yview_scroll(int(-1*(e.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_wheel)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return scroll_frame, canvas

def build_minecraft_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=8)
    inner, _ = _scrollable(frame)
    if not catalog or not catalog.minecraft_versions:
        ttk.Label(inner, text="Nenhuma versão de Minecraft disponível.", style="TLabel", foreground=COLORS["text_muted"]).pack(pady=40)
        return frame
    for v in catalog.minecraft_versions:
        card = ResourceCard(inner, title=v.name, description=v.description, link=v.link, banner_url=v.banner, warning=v.warning)
        card.pack(fill="x", pady=6, padx=6)
    return frame
