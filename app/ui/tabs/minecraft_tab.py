import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.components.scrollable import ScrollableFrame
from app.ui.styles import COLORS, FONTS

def build_minecraft_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=0)
    # header + search (tema livre)
    header = ttk.Frame(frame, style="TFrame", padding=(12, 10, 12, 6))
    header.pack(fill="x")
    ttk.Label(header, text="Versões disponíveis", style="Section.TLabel").pack(side="left")
    count = len(catalog.minecraft_versions) if catalog and catalog.minecraft_versions else 0
    ttk.Label(header, text=f"{count} itens", style="Muted.TLabel", font=FONTS["small"]).pack(side="right")

    # busca (tema livre)
    search_frame = tk.Frame(frame, bg=COLORS["bg"], highlightthickness=0)
    search_frame.pack(fill="x", padx=12, pady=(0, 6))
    tk.Label(search_frame, text="🔍", bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left", padx=(0, 6))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, font=FONTS["small"])
    search_entry.pack(side="left", fill="x", expand=True)
    # placeholder
    search_entry.insert(0, "Buscar por nome ou descrição…")
    def _on_focus_in(e):
        if search_entry.get() == "Buscar por nome ou descrição…":
            search_entry.delete(0, "end")
            search_entry.configure(foreground=COLORS["text_primary"])
    def _on_focus_out(e):
        if not search_entry.get().strip():
            search_entry.delete(0, "end")
            search_entry.insert(0, "Buscar por nome ou descrição…")
            search_entry.configure(foreground=COLORS["text_muted"])
    search_entry.bind("<FocusIn>", _on_focus_in)
    search_entry.bind("<FocusOut>", _on_focus_out)
    search_entry.configure(foreground=COLORS["text_muted"])
    clear_btn = ttk.Button(search_frame, text="✕", width=3, style="Ghost.TButton", command=lambda: (search_var.set(""), search_entry.delete(0, "end"), search_entry.insert(0, "Buscar por nome ou descrição…"), search_entry.configure(foreground=COLORS["text_muted"])))
    clear_btn.pack(side="left", padx=(6, 0))

    sc = ScrollableFrame(frame)
    sc.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    inner = sc.inner

    if not catalog or not catalog.minecraft_versions:
        empty = ttk.Frame(inner, style="Card.TFrame", padding=20)
        empty.pack(fill="x", padx=12, pady=24)
        try:
            from pathlib import Path
            from PIL import Image, ImageTk
            p = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "empty.png"
            if p.exists():
                img = Image.open(p)
                tk_img = ImageTk.PhotoImage(img)
                lbl = tk.Label(empty, image=tk_img, bg=COLORS["bg_card"], bd=0)
                lbl.image = tk_img
                lbl.pack(pady=(8, 12))
        except Exception:
            pass
        ttk.Label(empty, text="Nenhuma versão de Minecraft disponível.", style="Card.TLabel", font=FONTS["subtitle"]).pack()
        ttk.Label(empty, text="Tente atualizar o catálogo ou verifique o arquivo debug.", style="CardMuted.TLabel", font=FONTS["small"]).pack(pady=(4, 0))
        return frame

    # cards + searchable index
    cards = []
    for v in catalog.minecraft_versions:
        card = ResourceCard(inner, title=v.name, description=v.description, link=v.link, banner_url=v.banner, warning=v.warning)
        card.pack(fill="x", padx=12, pady=6)
        searchable = f"{v.name} {v.description} {v.id}".lower()
        cards.append((card, searchable))

    no_result = ttk.Label(inner, text="Nenhum resultado para a busca.", style="Muted.TLabel", font=FONTS["small"])
    # filtro
    def _filter(*args):
        q = search_var.get().strip().lower()
        if q == "buscar por nome ou descrição…":
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
        # atualiza scrollregion
        sc._update_scrollregion()

    search_var.trace_add("write", lambda *_: _filter())
    search_entry.bind("<KeyRelease>", lambda e: _filter() if e.keysym not in ("Up","Down") else None)

    ttk.Frame(inner, style="TFrame", height=8).pack(fill="x")
    return frame
