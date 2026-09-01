import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.styles import COLORS, FONTS

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

def build_libraries_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=8)
    inner = _scrollable(frame)
    if not catalog or not catalog.libraries:
        ttk.Label(inner, text="Nenhuma biblioteca compartilhada configurada.", style="TLabel", foreground=COLORS["text_muted"]).pack(pady=40)
        return frame

    libs = catalog.libraries
    # libs is dict; try to extract display fields
    name = libs.get("name") or libs.get("title") or "Bibliotecas Compartilhadas"
    description = libs.get("description") or libs.get("desc") or "Pacote global de bibliotecas compartilhadas entre versões."
    link = libs.get("link") or libs.get("url") or ""
    banner = libs.get("banner") or ""
    warning = libs.get("warning") or ""

    # if libs has only link/url, show generic card; otherwise show card + raw info
    card = ResourceCard(inner, title=str(name), description=str(description), link=str(link), banner_url=str(banner), warning=str(warning))
    card.pack(fill="x", pady=6, padx=6)

    # if there are extra keys, show as muted detail
    extra = {k: v for k, v in libs.items() if k not in ("name", "title", "description", "desc", "link", "url", "banner", "warning")}
    if extra:
        detail = ttk.Frame(inner, style="Card.TFrame", padding=12)
        detail.pack(fill="x", pady=6, padx=6)
        ttk.Label(detail, text="Detalhes adicionais:", style="Card.TLabel", font=FONTS["small"]).pack(anchor="w")
        for k, v in extra.items():
            ttk.Label(detail, text=f"{k}: {v}", style="CardSecondary.TLabel", font=FONTS["small"], wraplength=680).pack(anchor="w", pady=1)

    # Notice about reinstall if warning present is already shown in card; spec says present clear notice if libraries changed -> use warning text exactly
    return frame
