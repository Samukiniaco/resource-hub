import tkinter as tk
from tkinter import ttk

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.components.scrollable import ScrollableFrame
from app.ui.styles import COLORS, FONTS

def build_minecraft_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=0)
    # header inside tab
    header = ttk.Frame(frame, style="TFrame", padding=(12, 10, 12, 6))
    header.pack(fill="x")
    ttk.Label(header, text="Versões disponíveis", style="Section.TLabel").pack(side="left")
    count = len(catalog.minecraft_versions) if catalog and catalog.minecraft_versions else 0
    ttk.Label(header, text=f"{count} itens", style="Muted.TLabel", font=FONTS["small"]).pack(side="right")

    sc = ScrollableFrame(frame)
    sc.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    inner = sc.inner

    if not catalog or not catalog.minecraft_versions:
        # empty state com ícone
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

    for v in catalog.minecraft_versions:
        card = ResourceCard(inner, title=v.name, description=v.description, link=v.link, banner_url=v.banner, warning=v.warning)
        card.pack(fill="x", padx=12, pady=6)
    # spacer final para não colar no fim
    ttk.Frame(inner, style="TFrame", height=8).pack(fill="x")
    return frame
