import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

from app.models.catalog import Catalog
from app.config import get_catalog_url
from app.ui.styles import COLORS, FONTS
from app.utils.browser import open_url
from app.utils.clipboard import copy_to_clipboard
from app.ui.components.scrollable import ScrollableFrame
from app.services.history_service import fetch_history_async
from app.utils.logger import get_logger

logger = get_logger(__name__)

def _build_history_row(hist_inner, e, total, status_var, sc, inner):
    """Uma linha do histórico — escopo próprio, sem closure vazando."""
    row = tk.Frame(hist_inner, bg=COLORS["bg"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    row.pack(fill="x", pady=6)
    r = tk.Frame(row, bg=COLORS["bg"])
    r.pack(fill="x", padx=12, pady=10)
    head = tk.Frame(r, bg=COLORS["bg"])
    head.pack(fill="x")
    tk.Label(head, text=f"v{e.catalog_version}", bg=COLORS["bg"], fg=COLORS["accent"], font=FONTS["small_bold"]).pack(side="left")
    tk.Label(head, text=f"  ·  {e.date}  ·  {e.short_sha}  ·  {e.author or '—'}", bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left")
    if e.message and e.message.strip().lower() not in (e.catalog_version.lower(),):
        tk.Label(r, text=e.message, bg=COLORS["bg"], fg=COLORS["text_secondary"], font=FONTS["small"], wraplength=560, justify="left", anchor="w").pack(anchor="w", pady=(2, 4))
    preview = e.changelog.strip().split("\n")
    preview_text = "\n".join(preview[:3])
    if len(preview) > 3:
        preview_text += " …"
    txt = tk.Text(r, wrap="word", height=3, bg=COLORS["bg_card"], fg=COLORS["text_secondary"], relief="flat", bd=0, padx=8, pady=6, font=FONTS["small"], highlightthickness=1, highlightbackground=COLORS["border"])
    txt.insert("1.0", preview_text)
    txt.configure(state="disabled")
    txt.pack(fill="x", pady=(2, 8))

    # botões primeiro (existem antes do toggle referenciá-los)
    btn_row2 = tk.Frame(r, bg=COLORS["bg"])
    btn_row2.pack(fill="x")
    state = {"open": False, "full": None}
    exp_btn = ttk.Button(btn_row2, text="Ver changelog completo", style="Ghost.TButton")
    exp_btn.pack(side="left")

    def _toggle():
        if not state["open"]:
            lines = e.changelog.count("\n") + 1
            h = max(6, min(30, lines + 1))
            full = tk.Text(r, wrap="word", bg=COLORS["bg"], fg=COLORS["text_secondary"], relief="flat", bd=0, padx=8, pady=8, font=FONTS["body"], highlightthickness=1, highlightbackground=COLORS["border"], height=h)
            full.insert("1.0", e.changelog)
            full.configure(state="disabled")
            full.pack(fill="x", pady=(0, 8), before=btn_row2)
            state["full"] = full
            exp_btn.configure(text="Recolher")
            state["open"] = True
        else:
            if state["full"] is not None:
                try:
                    state["full"].destroy()
                except tk.TclError:
                    pass
                state["full"] = None
            exp_btn.configure(text="Ver changelog completo")
            state["open"] = False
        try:
            sc._update_scrollregion()
        except Exception:
            pass

    exp_btn.configure(command=_toggle)

    def _copy_raw():
        ok = copy_to_clipboard(inner.winfo_toplevel(), e.raw_url)
        status_var.set("Raw copiado!" if ok else "Falha ao copiar")
        inner.after(1500, lambda: status_var.set(f"{total} versões"))
    def _open_raw():
        open_url(e.raw_url)
    def _download():
        try:
            import urllib.request, json as _js
            data = _js.loads(urllib.request.urlopen(urllib.request.Request(e.raw_url, headers={"User-Agent": "ResourceHub/1.0"}), timeout=10).read().decode("utf-8"))
            p = filedialog.asksaveasfilename(parent=inner, title="Salvar catálogo antigo", defaultextension=".json", initialfile=f"catalog-{e.catalog_version}-{e.short_sha}.json", filetypes=[("JSON", "*.json")])
            if p:
                P = __import__("pathlib").Path
                P(p).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                messagebox.showinfo("Baixado", f"Salvo em {p}", parent=inner)
        except Exception as ex:
            messagebox.showerror("Erro", str(ex), parent=inner)

    ttk.Button(btn_row2, text="Copiar Raw", style="Secondary.TButton", command=_copy_raw).pack(side="left", padx=4)
    ttk.Button(btn_row2, text="Abrir Raw", style="Secondary.TButton", command=_open_raw).pack(side="left", padx=4)
    ttk.Button(btn_row2, text="Baixar JSON", style="Secondary.TButton", command=_download).pack(side="left", padx=4)


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

    # --- Histórico bonitinho dentro de Atualizações ---
    hist_card = tk.Frame(inner, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    hist_card.pack(fill="x", padx=12, pady=10)
    hc = tk.Frame(hist_card, bg=COLORS["bg_card"])
    hc.pack(fill="x", padx=16, pady=12)
    top = tk.Frame(hc, bg=COLORS["bg_card"])
    top.pack(fill="x")
    tk.Label(top, text="📜 Histórico de atualizações", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=FONTS["subtitle"]).pack(side="left")
    status_var = tk.StringVar(value="Carregando…")
    tk.Label(top, textvariable=status_var, bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="right")

    # container para entries
    hist_inner = tk.Frame(hc, bg=COLORS["bg_card"])
    hist_inner.pack(fill="x", pady=(8, 0))

    # placeholder enquanto carrega
    loading = tk.Label(hist_inner, text="Buscando commits em github.com/Samukiniaco/resource-hub…", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small"])
    loading.pack(anchor="w", pady=6)

    def _render_history(entries):
        def _ui():
            loading.pack_forget()
            if not entries:
                tk.Label(hist_inner, text="Nenhum histórico encontrado (offline?).", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(anchor="w")
                ttk.Button(hist_inner, text="Abrir commits no GitHub", style="Ghost.TButton", command=lambda: open_url("https://github.com/Samukiniaco/resource-hub/commits/master/data/catalog.json")).pack(anchor="w", pady=4)
                status_var.set("Offline")
                return
            status_var.set(f"{len(entries)} versões")
            for entry in entries:
                _build_history_row(hist_inner, entry, len(entries), status_var, sc, inner)

            # botão abrir todos no github
            ttk.Button(hist_inner, text="Ver todos os commits no GitHub", style="Ghost.TButton", command=lambda: open_url("https://github.com/Samukiniaco/resource-hub/commits/master/data/catalog.json")).pack(anchor="w", pady=(8, 0))
        inner.after(0, _ui)

    def _on_error(msg):
        def _ui():
            loading.configure(text=f"Offline — histórico no cache ({msg[:60]})" if "cache" not in msg.lower() else f"Falha: {msg[:60]}")
            status_var.set("Offline")
        inner.after(0, _ui)

    # dispara async
    try:
        fetch_history_async(_render_history, _on_error, limit=20)
    except Exception as ex:
        logger.warning("history fetch failed: %s", ex)
        loading.configure(text="Histórico indisponível")

    # footer
    ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=12, pady=12)
    tk.Label(inner, text="Launcher externo não é modificado, embutido ou distribuído por este app.",
             bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="w", padx=16, pady=(0, 2))
    tk.Label(inner, text="© Resource Hub — utilitário leve, sem rastreamento, sem execução automática.",
             bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="w", padx=16, pady=(0, 12))

    return frame
