import tkinter as tk
from tkinter import ttk
import re

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.components.scrollable import ScrollableFrame
from app.ui.styles import COLORS, FONTS

def _version_key(s: str):
    # natural sort para versões tipo 1.20.1, 26.2, c0.30_01c, rd-132211, 26.3-pre-1
    parts = re.split(r"[.\-_\s]+", s.lower())
    key = []
    for p in parts:
        if p.isdigit():
            key.append((0, int(p)))
        elif p:
            # tenta extrair número dentro de string tipo c0
            m = re.match(r"([a-z]*)(\d+)(.*)", p)
            if m:
                key.append((1, m.group(1)))
                key.append((0, int(m.group(2))))
                if m.group(3):
                    key.append((1, m.group(3)))
            else:
                key.append((1, p))
    return key

def build_minecraft_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=0)
    header = ttk.Frame(frame, style="TFrame", padding=(12, 10, 12, 6))
    header.pack(fill="x")
    ttk.Label(header, text="Versões disponíveis", style="Section.TLabel").pack(side="left")
    count = len(catalog.minecraft_versions) if catalog and catalog.minecraft_versions else 0
    ttk.Label(header, text=f"{count} itens", style="Muted.TLabel", font=FONTS["small"]).pack(side="right")

    # busca
    search_frame = tk.Frame(frame, bg=COLORS["bg"], highlightthickness=0)
    search_frame.pack(fill="x", padx=12, pady=(0, 4))
    tk.Label(search_frame, text="🔍", bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left", padx=(0, 6))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, font=FONTS["small"])
    search_entry.pack(side="left", fill="x", expand=True)
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

    # filtros (tema livre + pedido: ID e ordenação)
    filter_frame = tk.Frame(frame, bg=COLORS["bg"], highlightthickness=0)
    filter_frame.pack(fill="x", padx=12, pady=(0, 6))
    tk.Label(filter_frame, text="ID:", bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left")
    id_var = tk.StringVar(value="Todos")
    ids = sorted({v.id for v in (catalog.minecraft_versions if catalog else [])}, key=_version_key)
    id_combo = ttk.Combobox(filter_frame, textvariable=id_var, values=["Todos"] + ids, state="readonly", width=14, font=FONTS["small"])
    id_combo.pack(side="left", padx=(4, 12))
    tk.Label(filter_frame, text="Ordem:", bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left")
    sort_var = tk.StringVar(value="Catálogo")
    sort_opts = ["Catálogo", "A-Z (nome)", "Z-A (nome)", "Versão ↓", "Versão ↑", "ID A-Z", "ID Z-A"]
    sort_combo = ttk.Combobox(filter_frame, textvariable=sort_var, values=sort_opts, state="readonly", width=14, font=FONTS["small"])
    sort_combo.pack(side="left", padx=4)

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

    # dados + cards
    items = list(catalog.minecraft_versions)
    cards = []  # list of (card, searchable, version_obj)
    for v in items:
        card = ResourceCard(inner, title=v.name, description=v.description, link=v.link, banner_url=v.banner, warning=v.warning)
        # não pack ainda, será no filtro
        searchable = f"{v.name} {v.description} {v.id}".lower()
        cards.append((card, searchable, v))

    no_result = ttk.Label(inner, text="Nenhum resultado para os filtros.", style="Muted.TLabel", font=FONTS["small"])

    def _apply_filters():
        q = search_var.get().strip().lower()
        if q == "buscar por nome ou descrição…":
            q = ""
        idf = id_var.get().strip()
        sort = sort_var.get().strip()

        # filtra
        filtered = []
        for card, text, v in cards:
            if q and q not in text:
                continue
            if idf != "Todos" and v.id != idf:
                continue
            filtered.append((card, text, v))

        # ordena
        if sort == "A-Z (nome)":
            filtered.sort(key=lambda x: x[2].name.lower())
        elif sort == "Z-A (nome)":
            filtered.sort(key=lambda x: x[2].name.lower(), reverse=True)
        elif sort == "Versão ↓":
            filtered.sort(key=lambda x: _version_key(x[2].id), reverse=True)
        elif sort == "Versão ↑":
            filtered.sort(key=lambda x: _version_key(x[2].id))
        elif sort == "ID A-Z":
            filtered.sort(key=lambda x: x[2].id.lower())
        elif sort == "ID Z-A":
            filtered.sort(key=lambda x: x[2].id.lower(), reverse=True)
        # else Catálogo mantém ordem original filtrada (já está)

        # repack: esconde todos, mostra filtrados na ordem
        for card, _, _ in cards:
            card.pack_forget()
        no_result.pack_forget()
        if not filtered:
            no_result.pack(pady=20)
        else:
            for card, _, _ in filtered:
                card.pack(fill="x", padx=12, pady=6)
        # spacer
        # remove spacer antigo e recria? simplifica: garante no fim
        sc._update_scrollregion()

    # eventos
    search_var.trace_add("write", lambda *_: _apply_filters())
    search_entry.bind("<KeyRelease>", lambda e: _apply_filters() if e.keysym not in ("Up","Down") else None)
    id_combo.bind("<<ComboboxSelected>>", lambda e: _apply_filters())
    sort_combo.bind("<<ComboboxSelected>>", lambda e: _apply_filters())

    _apply_filters()
    ttk.Frame(inner, style="TFrame", height=8).pack(fill="x")
    return frame
