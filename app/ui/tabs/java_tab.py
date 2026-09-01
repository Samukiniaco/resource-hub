import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.components.scrollable import ScrollableFrame
from app.ui.styles import COLORS, FONTS
from app.services.java_helper import find_java_exes, locate_vortex_conf, update_java_path
from app.utils.logger import get_logger

logger = get_logger(__name__)

def build_java_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=0)

    # helper fixo no topo (não rola)
    helper = tk.Frame(frame, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    helper.pack(fill="x", padx=8, pady=8)
    inner_h = tk.Frame(helper, bg=COLORS["bg_card"])
    inner_h.pack(fill="x", padx=14, pady=12)
    top = tk.Frame(inner_h, bg=COLORS["bg_card"])
    top.pack(fill="x")
    tk.Label(top, text="⬢", fg=COLORS["accent"], bg=COLORS["bg_card"], font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 8))
    tk.Label(top, text="JavaPath Helper  —  vortex_launcher.conf", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=FONTS["subtitle"]).pack(side="left")
    tk.Label(inner_h, text="Selecione a pasta do Java. O app busca java.exe recursivamente e atualiza apenas a linha JavaPath, preservando comentários.",
             bg=COLORS["bg_card"], fg=COLORS["text_secondary"], font=FONTS["small"], wraplength=640, justify="left", anchor="w").pack(anchor="w", pady=(6, 10))

    def _on_java_helper():
        directory = filedialog.askdirectory(title="Selecione a pasta de instalação do Java", parent=frame)
        if not directory:
            return
        from pathlib import Path
        search_root = Path(directory)
        exes = find_java_exes(search_root)
        if not exes:
            messagebox.showerror("Java não encontrado", f"Nenhum java.exe em:\n{directory}", parent=frame)
            return
        chosen = None
        if len(exes) == 1:
            chosen = exes[0]
        else:
            chosen = _choose_java_dialog(frame, exes)
            if not chosen:
                return
        conf = locate_vortex_conf()
        if not conf:
            messagebox.showerror("Arquivo não encontrado", "vortex_launcher.conf não foi localizado próximo ao executável.", parent=frame)
            return
        ok, msg = update_java_path(conf, chosen)
        if ok:
            messagebox.showinfo("Sucesso", msg, parent=frame)
        else:
            messagebox.showerror("Erro", msg, parent=frame)

    def _choose_java_dialog(parent, exes):
        dlg = tk.Toplevel(parent)
        dlg.title("Selecione o java.exe")
        dlg.transient(parent); dlg.grab_set()
        dlg.configure(bg=COLORS["bg"])
        dlg.geometry("620x360")
        ttk.Label(dlg, text="Múltiplos java.exe encontrados:", style="TLabel").pack(padx=12, pady=(12, 6), anchor="w")
        listbox = tk.Listbox(dlg, bg=COLORS["bg_card"], fg=COLORS["text_primary"], selectbackground=COLORS["accent"], highlightthickness=0, bd=0, font=FONTS["small"])
        for p in exes:
            listbox.insert("end", str(p))
        listbox.pack(padx=12, pady=6, fill="both", expand=True)
        listbox.selection_set(0)
        result = {"path": None}
        def _ok():
            sel = listbox.curselection()
            if sel:
                result["path"] = exes[sel[0]]
            dlg.destroy()
        btns = ttk.Frame(dlg, style="TFrame")
        btns.pack(fill="x", padx=12, pady=12)
        ttk.Button(btns, text="Confirmar", style="Accent.TButton", command=_ok).pack(side="right", padx=4)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=dlg.destroy).pack(side="right")
        dlg.wait_window()
        return result["path"]

    btn_row = ttk.Frame(inner_h, style="Card.TFrame")
    btn_row.pack(anchor="w")
    ttk.Button(btn_row, text="Selecionar pasta do Java…", style="Accent.TButton", command=_on_java_helper).pack(side="left")
    tk.Label(btn_row, text="atualiza só JavaPath =", bg=COLORS["bg_card"], fg=COLORS["text_dim"], font=FONTS["mono"]).pack(side="left", padx=(10, 0))

    # lista rolável abaixo
    sc = ScrollableFrame(frame)
    sc.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    inner = sc.inner

    header2 = ttk.Frame(inner, style="TFrame", padding=(4, 6, 4, 2))
    header2.pack(fill="x", padx=8)
    ttk.Label(header2, text="Pacotes Java no catálogo", style="Section.TLabel").pack(side="left")
    count = len(catalog.java) if catalog and catalog.java else 0
    ttk.Label(header2, text=f"{count} itens", style="Muted.TLabel", font=FONTS["small"]).pack(side="right")

    # tema livre: busca java
    search_frame = tk.Frame(inner, bg=COLORS["bg"], highlightthickness=0)
    search_frame.pack(fill="x", padx=8, pady=(4, 6))
    tk.Label(search_frame, text="🔍", bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left", padx=(0, 6))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, font=FONTS["small"])
    search_entry.pack(side="left", fill="x", expand=True)
    search_entry.insert(0, "Buscar Java…")
    def _on_focus_in(e):
        if search_entry.get() == "Buscar Java…":
            search_entry.delete(0, "end")
            search_entry.configure(foreground=COLORS["text_primary"])
    def _on_focus_out(e):
        if not search_entry.get().strip():
            search_entry.delete(0, "end")
            search_entry.insert(0, "Buscar Java…")
            search_entry.configure(foreground=COLORS["text_muted"])
    search_entry.bind("<FocusIn>", _on_focus_in)
    search_entry.bind("<FocusOut>", _on_focus_out)
    search_entry.configure(foreground=COLORS["text_muted"])

    if not catalog or not catalog.java:
        empty = ttk.Frame(inner, style="Card.TFrame", padding=20)
        empty.pack(fill="x", padx=12, pady=12)
        ttk.Label(empty, text="Nenhum pacote Java configurado.", style="Card.TLabel", font=FONTS["subtitle"]).pack()
        return frame

    cards = []
    for j in catalog.java:
        card = ResourceCard(inner, title=j.name, description=j.description or f"Java {j.version}", link=j.link, banner_url="", warning="")
        card.pack(fill="x", padx=12, pady=6)
        searchable = f"{j.name} {j.version} {j.description}".lower()
        cards.append((card, searchable))

    no_result = ttk.Label(inner, text="Nenhum resultado.", style="Muted.TLabel", font=FONTS["small"])
    def _filter(*args):
        q = search_var.get().strip().lower()
        if q == "buscar java…":
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
            no_result.pack(pady=12)
        else:
            no_result.pack_forget()
        sc._update_scrollregion()
    search_var.trace_add("write", lambda *_: _filter())

    ttk.Frame(inner, style="TFrame", height=8).pack(fill="x")
    return frame
