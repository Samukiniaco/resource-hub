"""Main window — branding + status + 5 tabs. Scroll corrigido."""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from app.config import get_catalog_url, APP_TITLE, APP_GEOMETRY, PROJECT_ROOT
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
        self.root.minsize(880, 620)
        apply_theme(self.root)
        self._set_icon()

        self.catalog: Catalog | None = None
        self.status_var = tk.StringVar(value="Carregando catálogo…")
        self.status_dot_var = tk.StringVar(value="●")

        # Top bar — branding
        top = tk.Frame(self.root, bg=COLORS["bg_top"], bd=0, highlightthickness=0)
        top.pack(fill="x")
        # logo + title
        left = tk.Frame(top, bg=COLORS["bg_top"])
        left.pack(side="left", padx=12, pady=8)
        # icon image if available
        try:
            from PIL import Image, ImageTk
            icon_path = PROJECT_ROOT / "assets" / "icon.png"
            if icon_path.exists():
                img = Image.open(icon_path).resize((28, 28), Image.LANCZOS)
                self._icon_img = ImageTk.PhotoImage(img)
                tk.Label(left, image=self._icon_img, bg=COLORS["bg_top"], bd=0).pack(side="left", padx=(0, 8))
        except Exception:
            pass
        tk.Label(left, text="Resource Hub", bg=COLORS["bg_top"], fg=COLORS["text_primary"], font=FONTS["brand"]).pack(side="left")
        tk.Label(left, text="  ·  recursos do launcher", bg=COLORS["bg_top"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left", padx=(8, 0))

        # actions
        right = tk.Frame(top, bg=COLORS["bg_top"])
        right.pack(side="right", padx=12, pady=8)
        self.open_url_btn = ttk.Button(right, text="Abrir URL do catálogo", style="Ghost.TButton", command=self._open_catalog_url)
        self.open_url_btn.pack(side="right", padx=(8, 0))
        self.refresh_btn = ttk.Button(right, text="Atualizar catálogo", style="Secondary.TButton", command=self.refresh_catalog)
        self.refresh_btn.pack(side="right")

        # status bar (subtle under top)
        status_bar = tk.Frame(self.root, bg=COLORS["bg_top"], bd=0, highlightthickness=0)
        status_bar.pack(fill="x")
        ttk.Separator(status_bar, orient="horizontal").pack(fill="x")
        inner_sb = tk.Frame(status_bar, bg=COLORS["bg_top"])
        inner_sb.pack(fill="x", padx=12, pady=4)
        self.dot_label = tk.Label(inner_sb, textvariable=self.status_dot_var, bg=COLORS["bg_top"], fg=COLORS["text_muted"], font=("Segoe UI", 8))
        self.dot_label.pack(side="left", padx=(0, 6))
        tk.Label(inner_sb, textvariable=self.status_var, bg=COLORS["bg_top"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left")

        # notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._load_cached()
        self._build_tabs()
        self.root.after(800, self.refresh_catalog)

    def _set_icon(self):
        try:
            icon = PROJECT_ROOT / "assets" / "icon.png"
            if icon.exists():
                self.root.iconphoto(True, tk.PhotoImage(file=str(icon)))
        except Exception:
            pass

    def _load_cached(self):
        cat, err = load_cached_catalog()
        if cat:
            self.catalog = cat
            self.status_var.set(f"Catálogo local v{cat.catalog_version} carregado")
            self.dot_label.configure(fg=COLORS["status_ok"])
            self.status_dot_var.set("●")
            logger.info("Loaded cached v%s", cat.catalog_version)
        else:
            self.status_var.set(err or "Sem catálogo local")
            self.dot_label.configure(fg=COLORS["status_warn"])

    def _build_tabs(self):
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        mc = build_minecraft_tab(self.notebook, self.catalog)
        libs = build_libraries_tab(self.notebook, self.catalog)
        java = build_java_tab(self.notebook, self.catalog)
        other = build_other_tab(self.notebook, self.catalog)
        updates = build_updates_tab(self.notebook, self.catalog)
        self.notebook.add(mc, text="  Minecraft  ")
        self.notebook.add(libs, text="  Bibliotecas  ")
        self.notebook.add(java, text="  Java  ")
        self.notebook.add(other, text="  Outros / Patches  ")
        self.notebook.add(updates, text="  Atualizações  ")

    def _open_catalog_url(self):
        open_url(get_catalog_url())

    def refresh_catalog(self):
        self.status_var.set("Atualizando catálogo…")
        self.dot_label.configure(fg=COLORS["accent"])
        self.refresh_btn.configure(state="disabled")

        def on_success(new_cat: Catalog, old_cat: Catalog | None, changelog: str):
            def _ui():
                self.catalog = new_cat
                self._build_tabs()
                if old_cat and old_cat.catalog_version != new_cat.catalog_version and changelog:
                    self.status_var.set(f"Atualizado para v{new_cat.catalog_version} — veja Atualizações")
                    self.dot_label.configure(fg=COLORS["status_ok"])
                    self._show_update_notice(new_cat, changelog)
                elif old_cat and old_cat.catalog_version == new_cat.catalog_version:
                    self.status_var.set(f"Já atualizado (v{new_cat.catalog_version})")
                    self.dot_label.configure(fg=COLORS["status_ok"])
                else:
                    self.status_var.set(f"Catálogo v{new_cat.catalog_version} carregado")
                    self.dot_label.configure(fg=COLORS["status_ok"])
                    if changelog:
                        self._show_update_notice(new_cat, changelog)
                self.refresh_btn.configure(state="normal")
                if new_cat.libraries.get("warning"):
                    self._show_libraries_warning(new_cat.libraries["warning"])
            self.root.after(0, _ui)

        def on_error(msg: str):
            def _ui():
                self.status_var.set(f"Offline — usando cache local ({msg[:70]})")
                self.dot_label.configure(fg=COLORS["status_warn"])
                self.refresh_btn.configure(state="normal")
                logger.warning("Catalog update failed: %s", msg)
            self.root.after(0, _ui)

        update_async(on_success=on_success, on_error=on_error)

    def _show_update_notice(self, catalog: Catalog, changelog: str):
        try:
            dlg = tk.Toplevel(self.root)
            dlg.title(f"Atualização — v{catalog.catalog_version}")
            dlg.transient(self.root); dlg.grab_set()
            dlg.configure(bg=COLORS["bg"])
            dlg.geometry("580x400")
            dlg.minsize(520, 340)
            header = tk.Frame(dlg, bg=COLORS["bg_card"], bd=0)
            header.pack(fill="x", padx=1, pady=1)
            h = tk.Frame(header, bg=COLORS["bg_card"])
            h.pack(fill="x", padx=14, pady=12)
            tk.Label(h, text="✦  Nova versão disponível", bg=COLORS["bg_card"], fg=COLORS["accent"], font=FONTS["small_bold"]).pack(anchor="w")
            tk.Label(h, text=f"v{catalog.catalog_version}", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(4, 0))
            tk.Label(h, text="Notas de atualização:", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=FONTS["small"]).pack(anchor="w", pady=(8, 0))
            txt = tk.Text(dlg, wrap="word", bg=COLORS["bg"], fg=COLORS["text_secondary"], relief="flat", bd=0,
                          padx=12, pady=12, font=FONTS["body"], highlightthickness=1, highlightbackground=COLORS["border"])
            txt.insert("1.0", changelog or "Sem detalhes.")
            txt.configure(state="disabled")
            txt.pack(fill="both", expand=True, padx=1, pady=0)
            btns = ttk.Frame(dlg, style="TFrame", padding=12)
            btns.pack(fill="x")
            ttk.Button(btns, text="Continuar", style="Accent.TButton", command=dlg.destroy).pack(side="right")
        except Exception as e:
            logger.warning("Update notice failed: %s", e)

    def _show_libraries_warning(self, warning: str):
        if not warning:
            return
        self.root.after(1500, lambda: messagebox.showwarning("Bibliotecas", warning, parent=self.root))
