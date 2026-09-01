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

    # tema livre: busca
    search_frame = tk.Frame(frame, bg=COLORS["bg"], highlightthickness=0)
    search_frame.pack(fill="x", padx=12, pady=(0, 6))
    tk.Label(search_frame, text="🔍", bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left", padx=(0, 6))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, font=FONTS["small"])
    search_entry.pack(side="left", fill="x", expand=True)
    search_entry.insert(0, "Buscar patch por nome, categoria…")
    def _on_focus_in(e):
        if search_entry.get() == "Buscar patch por nome, categoria…":
            search_entry.delete(0, "end")
            search_entry.configure(foreground=COLORS["text_primary"])
    def _on_focus_out(e):
        if not search_entry.get().strip():
            search_entry.delete(0, "end")
            search_entry.insert(0, "Buscar patch por nome, categoria…")
            search_entry.configure(foreground=COLORS["text_muted"])
    search_entry.bind("<FocusIn>", _on_focus_in)
    search_entry.bind("<FocusOut>", _on_focus_out)
    search_entry.configure(foreground=COLORS["text_muted"])

    sc = ScrollableFrame(frame)
    sc.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    inner = sc.inner

    if not catalog or not catalog.other:
        empty = ttk.Frame(inner, style="Card.TFrame", padding=20)
        empty.pack(fill="x", padx=12, pady=24)
        ttk.Label(empty, text="Nenhum patch ou arquivo adicional.", style="Card.TLabel", font=FONTS["subtitle"]).pack()
        ttk.Label(empty, text="Adicione entradas em 'other' no catálogo para aparecerem aqui.", style="CardMuted.TLabel", font=FONTS["small"]).pack(pady=(4, 0))
        return frame

    cards = []
    for o in catalog.other:
        title = f"{o.name}  ·  {o.category}" if o.category and o.category != "other" else o.name
        card = ResourceCard(inner, title=title, description=o.description, link=o.link, banner_url=o.banner, warning=o.warning)
        card.pack(fill="x", padx=12, pady=6)
        searchable = f"{o.name} {o.category} {o.description}".lower()
        cards.append((card, searchable))

    no_result = ttk.Label(inner, text="Nenhum resultado.", style="Muted.TLabel", font=FONTS["small"])
    def _filter(*args):
        q = search_var.get().strip().lower()
        if q == "buscar patch por nome, categoria…":
            q = ""
        visible = 0
        for card, text in cards:
            show = not q or q in text
            if show:
                card.pack(fill="x", padx=12, pady=6)
                visible += 1
            else:
                card.pack_forget()
        if visible == 0 and q:
            no_result.pack(pady=20)
        else:
            no_result.pack_forget()
        sc._update_scrollregion()
    search_var.trace_add("write", lambda *_: _filter())
    ttk.Frame(inner, style="TFrame", height=8).pack(fill="x")
    return frame
