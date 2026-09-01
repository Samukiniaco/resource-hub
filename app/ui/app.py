"""Main window with 5 tabs, async catalog refresh, non-intrusive status."""
import tkinter as tk
from tkinter import ttk, messagebox

from app.config import get_catalog_url, APP_TITLE, APP_GEOMETRY
from app.models.catalog import Catalog
from app.services.catalog_service import load_cached_catalog, update_async
from app.ui.styles import apply_theme, COLORS, FONTS
from app.utils.browser import open_url
from app.utils.logger import get_logger
from app.ui.tabs.minecraft_tab import build_minecraft_tab
from app.ui.tabs.libraries_tab import build_libraries_tab
from app.ui.tabs.java_tab import build_java_tab
from app.ui.tabs.other_tab import build_other_tab
from app.ui.tabs.updates_tab import build_updates_tab

logger = get_logger(__name__)

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)
        self.root.minsize(860, 560)
        apply_theme(self.root)

        self.catalog: Catalog | None = None
        self.status_var = tk.StringVar(value="Carregando catálogo...")

        # Top bar: status + actions
        top = ttk.Frame(self.root, style="TFrame", padding=(12, 8))
        top.pack(fill="x")
        self.status_label = ttk.Label(top, textvariable=self.status_var, style="TLabel", font=FONTS["small"], foreground=COLORS["text_muted"])
        self.status_label.pack(side="left")
        self.refresh_btn = ttk.Button(top, text="Atualizar catálogo", style="Secondary.TButton", command=self.refresh_catalog)
        self.refresh_btn.pack(side="right", padx=(8, 0))
        self.open_url_btn = ttk.Button(top, text="Abrir URL do catálogo", style="Secondary.TButton", command=self._open_catalog_url)
        self.open_url_btn.pack(side="right")

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # initial load
        self._load_cached()
        self._build_tabs()
        # async refresh on start
        self.root.after(800, self.refresh_catalog)

    def _load_cached(self):
        cat, err = load_cached_catalog()
        if cat:
            self.catalog = cat
            self.status_var.set(f"Catálogo local v{cat.catalog_version} carregado.")
            logger.info("Loaded cached catalog v%s", cat.catalog_version)
        else:
            self.status_var.set(err or "Sem catálogo local.")
            logger.warning("No catalog: %s", err)

    def _build_tabs(self):
        # clear
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        # rebuild
        mc = build_minecraft_tab(self.notebook, self.catalog)
        libs = build_libraries_tab(self.notebook, self.catalog)
        java = build_java_tab(self.notebook, self.catalog)
        other = build_other_tab(self.notebook, self.catalog)
        updates = build_updates_tab(self.notebook, self.catalog)

        self.notebook.add(mc, text=" Minecraft ")
        self.notebook.add(libs, text=" Bibliotecas ")
        self.notebook.add(java, text=" Java ")
        self.notebook.add(other, text=" Outros / Patches ")
        self.notebook.add(updates, text=" Atualizações ")

    def _open_catalog_url(self):
        url = get_catalog_url()
        open_url(url)

    def refresh_catalog(self):
        self.status_var.set("Atualizando catálogo...")
        self.refresh_btn.configure(state="disabled")
        url = get_catalog_url()

        def on_success(new_cat: Catalog, old_cat: Catalog | None, changelog: str):
            def _ui():
                self.catalog = new_cat
                self._build_tabs()
                if old_cat and old_cat.catalog_version != new_cat.catalog_version and changelog:
                    self.status_var.set(f"Atualizado para v{new_cat.catalog_version} — veja Atualizações")
                    self._show_update_notice(new_cat, changelog)
                elif old_cat and old_cat.catalog_version == new_cat.catalog_version:
                    self.status_var.set(f"Catálogo já atualizado (v{new_cat.catalog_version})")
                else:
                    self.status_var.set(f"Catálogo v{new_cat.catalog_version} carregado.")
                    if changelog:
                        self._show_update_notice(new_cat, changelog)
                self.refresh_btn.configure(state="normal")
                # show libraries warning if any
                if new_cat.libraries.get("warning"):
                    self._show_libraries_warning(new_cat.libraries["warning"])
            self.root.after(0, _ui)

        def on_error(msg: str):
            def _ui():
                # non-intrusive indicator, fallback already kept
                self.status_var.set(f"Não foi possível atualizar — usando cache local. ({msg[:80]})")
                self.refresh_btn.configure(state="normal")
                logger.warning("Catalog update failed: %s", msg)
            self.root.after(0, _ui)

        update_async(on_success=on_success, on_error=on_error)

    def _show_update_notice(self, catalog: Catalog, changelog: str):
        # non-blocking info dialog with changelog
        try:
            dlg = tk.Toplevel(self.root)
            dlg.title(f"Catálogo atualizado — v{catalog.catalog_version}")
            dlg.transient(self.root)
            dlg.grab_set()
            dlg.configure(bg=COLORS["bg"])
            dlg.geometry("560x380")
            ttk.Label(dlg, text=f"Nova versão disponível: {catalog.catalog_version}", style="TLabel", font=FONTS["title"]).pack(padx=12, pady=(12, 6), anchor="w")
            ttk.Label(dlg, text="Notas de atualização:", style="TLabel", font=FONTS["body"]).pack(padx=12, anchor="w")
            txt = tk.Text(dlg, wrap="word", bg=COLORS["bg_card"], fg=COLORS["text_secondary"], relief="flat", padx=8, pady=8, font=FONTS["body"])
            txt.insert("1.0", changelog or "Sem detalhes.")
            txt.configure(state="disabled")
            txt.pack(fill="both", expand=True, padx=12, pady=8)
            btns = ttk.Frame(dlg, style="TFrame")
            btns.pack(fill="x", padx=12, pady=12)
            def _dismiss():
                dlg.destroy()
            ttk.Button(btns, text="Continuar", style="Accent.TButton", command=_dismiss).pack(side="right")
            # allow dismiss freely per spec
        except Exception as e:
            logger.warning("Failed to show update notice: %s", e)

    def _show_libraries_warning(self, warning: str):
        if not warning:
            return
        self.root.after(1500, lambda: messagebox.showwarning("Bibliotecas", warning, parent=self.root))
