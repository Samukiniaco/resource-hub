import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from app.models.catalog import Catalog
from app.ui.components.card import ResourceCard
from app.ui.styles import COLORS
from app.services.java_helper import find_java_exes, locate_vortex_conf, update_java_path
from app.utils.logger import get_logger

logger = get_logger(__name__)

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

def build_java_tab(notebook: ttk.Notebook, catalog: Catalog | None) -> ttk.Frame:
    frame = ttk.Frame(notebook, style="TFrame", padding=8)

    # Top helper section
    helper = ttk.Frame(frame, style="Card.TFrame", padding=12)
    helper.pack(fill="x", padx=6, pady=(6, 12))
    ttk.Label(helper, text="JavaPath Helper — vortex_launcher.conf", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    ttk.Label(helper, text="Selecione a pasta do Java instalada. O app buscará java.exe e atualizará apenas a linha JavaPath, preservando o restante do arquivo.", style="CardSecondary.TLabel", wraplength=680, justify="left").pack(anchor="w", pady=(4, 8))

    def _on_java_helper():
        directory = filedialog.askdirectory(title="Selecione a pasta de instalação do Java", parent=frame)
        if not directory:
            return
        from pathlib import Path
        search_root = Path(directory)
        exes = find_java_exes(search_root)
        if not exes:
            messagebox.showerror("Java não encontrado", f"Nenhum java.exe encontrado em:\n{directory}", parent=frame)
            return
        chosen: Path | None = None
        if len(exes) == 1:
            chosen = exes[0]
        else:
            # multiple -> selection dialog
            chosen = _choose_java_dialog(frame, exes)
            if not chosen:
                return
        # locate conf
        conf = locate_vortex_conf()
        if not conf:
            messagebox.showerror("Arquivo não encontrado", "vortex_launcher.conf não foi localizado próximo ao executável.\nVerifique se o arquivo existe na mesma pasta do app.", parent=frame)
            return
        ok, msg = update_java_path(conf, chosen)
        if ok:
            messagebox.showinfo("Sucesso", msg, parent=frame)
        else:
            messagebox.showerror("Erro", msg, parent=frame)

    def _choose_java_dialog(parent, exes):
        dlg = tk.Toplevel(parent)
        dlg.title("Selecione o java.exe")
        dlg.transient(parent)
        dlg.grab_set()
        dlg.configure(bg=COLORS["bg"])
        ttk.Label(dlg, text="Múltiplos java.exe encontrados. Escolha um:", style="TLabel").pack(padx=12, pady=(12, 6), anchor="w")
        listbox = tk.Listbox(dlg, width=80, height=min(len(exes), 10), bg=COLORS["bg_card"], fg=COLORS["text_primary"], selectbackground=COLORS["accent"])
        for p in exes:
            listbox.insert("end", str(p))
        listbox.pack(padx=12, pady=6, fill="both", expand=True)
        listbox.selection_set(0)
        result: dict = {"path": None}
        def _ok():
            sel = listbox.curselection()
            if sel:
                result["path"] = exes[sel[0]]
            dlg.destroy()
        def _cancel():
            dlg.destroy()
        btns = ttk.Frame(dlg, style="TFrame")
        btns.pack(fill="x", padx=12, pady=12)
        ttk.Button(btns, text="Confirmar", style="Accent.TButton", command=_ok).pack(side="right", padx=4)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=_cancel).pack(side="right")
        dlg.wait_window()
        return result["path"]

    ttk.Button(helper, text="Selecionar pasta do Java...", style="Accent.TButton", command=_on_java_helper).pack(anchor="w", pady=(4, 0))

    # Catalog java resources below
    inner = _scrollable(frame)
    if not catalog or not catalog.java:
        ttk.Label(inner, text="Nenhum pacote Java configurado no catálogo.", style="TLabel", foreground=COLORS["text_muted"]).pack(pady=30)
        return frame
    for j in catalog.java:
        card = ResourceCard(inner, title=j.name, description=j.description or f"Java {j.version}", link=j.link, banner_url="", warning="")
        card.pack(fill="x", pady=6, padx=6)
    return frame
