#!/usr/bin/env python3
"""
Catalog Editor — programinha para edição fácil do catálogo global.

Foco: conteúdo global de updates (app.catalog_version + changelog) mas permite
editar todo o catálogo (minecraft, libraries, java, other) sem editar JSON na mão.

Uso:
    python tools/catalog_editor.py
    python tools/catalog_editor.py data/catalog.json
    python tools/catalog_editor.py tests/debug/catalog.json

- Valida com app.models.catalog.validate_catalog antes de salvar.
- Nunca executa links; apenas valida URLs http/https.
- Ideal para hospedagem externa: edite aqui e faça upload do JSON para nuvem.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from copy import deepcopy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from app.models.catalog import validate_catalog
    from app.config import DATA_DIR
except Exception as e:
    print(f"Erro importando app.models: {e}", file=sys.stderr)
    sys.exit(1)

DEFAULT_CANDIDATES = [
    PROJECT_ROOT / "data" / "catalog.json",
    PROJECT_ROOT / "tests" / "debug" / "catalog.json",
    PROJECT_ROOT / "data" / "catalog.example.json",
]

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def bump_patch(version: str) -> str:
    parts = version.strip().split(".")
    try:
        while len(parts) < 3:
            parts.append("0")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    except Exception:
        return version

class CatalogEditor(tk.Tk):
    def __init__(self, initial_path: Path | None = None):
        super().__init__()
        self.title("Resource Hub — Catalog Editor")
        self.geometry("980x720")
        self.minsize(860, 600)
        self.catalog: dict = {}
        self.current_path: Path | None = None
        self._saved_snapshot: str = ""
        self._dirty: bool = False

        # style light for editor (different from dark app)
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # top bar
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Arquivo:").pack(side="left")
        self.path_var = tk.StringVar(value=str(initial_path) if initial_path else "")
        self.path_entry = ttk.Entry(top, textvariable=self.path_var, width=60)
        self.path_entry.pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(top, text="Abrir…", command=self.open_dialog).pack(side="left", padx=2)
        ttk.Button(top, text="Salvar", command=self.save).pack(side="left", padx=2)
        ttk.Button(top, text="Salvar como…", command=self.save_as).pack(side="left", padx=2)
        ttk.Button(top, text="Validar", command=self.validate).pack(side="left", padx=6)

        # main notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Tab 1: App / Global Updates ---
        self.tab_app = ttk.Frame(nb, padding=12)
        nb.add(self.tab_app, text=" App / Updates (global) ")
        self._build_app_tab(self.tab_app)

        # --- Tab 2: Minecraft ---
        self.tab_mc = ttk.Frame(nb, padding=8)
        nb.add(self.tab_mc, text=" Minecraft ")
        self._build_list_tab(self.tab_mc, "minecraft")

        # --- Tab 3: Libraries ---
        self.tab_libs = ttk.Frame(nb, padding=12)
        nb.add(self.tab_libs, text=" Bibliotecas (global) ")
        self._build_libs_tab(self.tab_libs)

        # --- Tab 4: Java ---
        self.tab_java = ttk.Frame(nb, padding=8)
        nb.add(self.tab_java, text=" Java ")
        self._build_list_tab(self.tab_java, "java")

        # --- Tab 5: Other ---
        self.tab_other = ttk.Frame(nb, padding=8)
        nb.add(self.tab_other, text=" Outros / Patches ")
        self._build_list_tab(self.tab_other, "other")

        # --- Tab 6: Raw JSON ---
        self.tab_raw = ttk.Frame(nb, padding=8)
        nb.add(self.tab_raw, text=" JSON Bruto ")
        self.raw_text = tk.Text(self.tab_raw, wrap="none", font=("Consolas", 9))
        self.raw_text.pack(fill="both", expand=True)
        ttk.Button(self.tab_raw, text="Carregar do editor bruto → memória", command=self.load_from_raw).pack(pady=6)

        # status
        self.status = tk.StringVar(value="Pronto.")
        ttk.Label(self, textvariable=self.status, anchor="w", padding=(8, 4)).pack(fill="x")

        # tema livre: dicas rotativas + atalhos
        self._tips = [
            "Dica: Ctrl+S salva rapidamente • Ctrl+Q sai com confirmação",
            "Dica: Altere catalog_version para notificar todos os usuários",
            "Dica: Use 'Bump patch' para semântica de versão",
            "Dica: Banner vazio = card mais leve • Warning = destaque amarelo",
            "Dica: hospede o JSON no GitHub Raw e aponte RESOURCE_HUB_CATALOG_URL",
        ]
        import random as _rnd
        self._tip_var = tk.StringVar(value=_rnd.choice(self._tips))
        ttk.Label(self, textvariable=self._tip_var, anchor="w", padding=(8, 0), foreground="#666", font=("Segoe UI", 8, "italic")).pack(fill="x")
        self.after(8000, self._rotate_tip)

        # confirmação ao fechar + atalhos + tema livre
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind_all("<Control-s>", lambda e: self.save())
        self.bind_all("<Control-S>", lambda e: self.save())
        self.bind_all("<Control-q>", lambda e: self._on_close())
        # marcar dirty ao digitar nas áreas principais
        self._setup_dirty_tracking()

        # initial load
        if initial_path and initial_path.exists():
            self.load_path(initial_path)
        else:
            # try default
            for p in DEFAULT_CANDIDATES:
                if p.exists():
                    self.load_path(p)
                    break
            else:
                # create minimal catalog
                self.catalog = {
                    "schema_version": 1,
                    "app": {"catalog_version": "1.0.0", "changelog": ""},
                    "minecraft": {"versions": []},
                    "libraries": {},
                    "java": [],
                    "launcher": {},
                    "other": []
                }
                self.refresh_all()
                self._snapshot_saved()

    # ----- App tab -----
    def _build_app_tab(self, parent):
        ttk.Label(parent, text="Conteúdo GLOBAL de updates — exibido na aba Atualizações do app", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(parent, text="schema_version (fixo 1):").pack(anchor="w")
        self.schema_var = tk.StringVar(value="1")
        e = ttk.Entry(parent, textvariable=self.schema_var, width=10, state="readonly")
        e.pack(anchor="w", pady=(2, 8))

        ttk.Label(parent, text="catalog_version (ex: 1.0.1) — alterar dispara notificação de update:").pack(anchor="w")
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        self.version_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.version_var, width=20).pack(side="left")
        ttk.Button(row, text="Bump patch (+0.0.1)", command=self.bump_version).pack(side="left", padx=8)
        ttk.Label(parent, text="Dica: hospede o JSON em nuvem (GitHub Raw/S3) e o app detecta versão nova vs cache local.").pack(anchor="w", pady=(0, 8))

        ttk.Label(parent, text="changelog (exibido ao usuário quando há nova versão):").pack(anchor="w")
        self.changelog_text = tk.Text(parent, height=10, wrap="word", font=("Segoe UI", 9))
        self.changelog_text.pack(fill="both", expand=True, pady=4)

        ttk.Label(parent, text="launcher (opcional, ex: link do Vortex Launcher):").pack(anchor="w", pady=(8, 0))
        libs = ttk.Frame(parent)
        libs.pack(fill="x")
        ttk.Label(libs, text="Launcher nome:").pack(side="left")
        self.launcher_name_var = tk.StringVar()
        ttk.Entry(libs, textvariable=self.launcher_name_var, width=22).pack(side="left", padx=4)
        ttk.Label(libs, text="link:").pack(side="left", padx=(8, 0))
        self.launcher_link_var = tk.StringVar()
        ttk.Entry(libs, textvariable=self.launcher_link_var, width=40).pack(side="left", padx=4, fill="x", expand=True)

    def bump_version(self):
        self.version_var.set(bump_patch(self.version_var.get().strip() or "1.0.0"))
        self._mark_dirty()

    # ----- Tema livre: helpers dirty / tips / preview -----
    def _snapshot_saved(self):
        try:
            self._saved_snapshot = json.dumps(self.catalog, ensure_ascii=False, sort_keys=True)
            self._dirty = False
            self._update_title()
        except Exception:
            pass

    def _is_dirty(self) -> bool:
        try:
            # compara snapshot com estado atual (inclui edits não aplicados via sync_from_ui)
            cur = deepcopy(self.catalog)
            # simula sync_from_ui sem alterar self.catalog original para checagem
            tmp = json.loads(json.dumps(cur, ensure_ascii=False))
            # aplica campos de UI temporariamente
            tmp["schema_version"] = 1
            if "app" not in tmp:
                tmp["app"] = {}
            tmp["app"]["catalog_version"] = self.version_var.get().strip() if hasattr(self, "version_var") else tmp.get("app", {}).get("catalog_version", "")
            if hasattr(self, "changelog_text"):
                tmp["app"]["changelog"] = self.changelog_text.get("1.0", "end").strip()
            cur_dump = json.dumps(tmp, ensure_ascii=False, sort_keys=True)
            return cur_dump != self._saved_snapshot or self._dirty
        except Exception:
            return self._dirty

    def _mark_dirty(self, *args):
        if not self._dirty:
            self._dirty = True
            self._update_title()

    def _update_title(self):
        base = "Resource Hub — Catalog Editor"
        path_part = f" — {self.current_path.name}" if self.current_path else ""
        dirty_mark = " •" if self._is_dirty() else ""
        self.title(base + path_part + dirty_mark)

    def _rotate_tip(self):
        import random as _rnd
        self._tip_var.set(_rnd.choice(self._tips))
        self.after(10000, self._rotate_tip)

    def _setup_dirty_tracking(self):
        # rastreia mudanças nas variáveis e textos principais
        try:
            self.version_var.trace_add("write", lambda *_: self._mark_dirty())
            self.launcher_name_var.trace_add("write", lambda *_: self._mark_dirty())
            self.launcher_link_var.trace_add("write", lambda *_: self._mark_dirty())
        except Exception:
            pass
        for txt_attr in ("changelog_text", "libs_desc_text", "libs_warning_text", "raw_text"):
            try:
                widget = getattr(self, txt_attr, None)
                if widget is not None:
                    widget.bind("<KeyRelease>", lambda e: self._mark_dirty(), add="+")
                    widget.bind("<FocusOut>", lambda e: self._update_title(), add="+")
            except Exception:
                pass

    def _on_close(self):
        if self._is_dirty():
            resp = messagebox.askyesnocancel(
                "Alterações não salvas",
                "Há alterações não salvas no catálogo.\n\nDeseja salvar antes de sair?\n• Sim = Salvar e sair\n• Não = Sair sem salvar\n• Cancelar = Ficar no editor",
                parent=self,
            )
            if resp is None:  # Cancelar
                return
            if resp:  # Sim
                self.save()
                # se ainda dirty (falha ao salvar/validação cancelada), não fecha
                if self._is_dirty():
                    # usuário cancelou save ou falhou
                    return
        # tema livre: despedida sutil
        self.destroy()

    # ----- Libraries tab -----
    def _build_libs_tab(self, parent):
        ttk.Label(parent, text="Bibliotecas = recurso GLOBAL compartilhado (não duplique por versão)", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Label(parent, text="Se 'warning' for preenchido, o app exibe aviso de reinstalação.").pack(anchor="w", pady=(0, 8))
        for label, attr in [("Nome:", "libs_name"), ("Descrição:", "libs_desc"), ("Link:", "libs_link"), ("Warning (aviso de reinstalação):", "libs_warning"), ("Banner (URL opcional):", "libs_banner")]:
            ttk.Label(parent, text=label).pack(anchor="w", pady=(4, 0))
            var = tk.StringVar()
            setattr(self, attr + "_var", var)
            if "Descrição" in label or "Warning" in label:
                txt = tk.Text(parent, height=3, wrap="word", font=("Segoe UI", 9))
                setattr(self, attr + "_text", txt)
                txt.pack(fill="x", pady=2)
            else:
                ttk.Entry(parent, textvariable=var).pack(fill="x", pady=2)

    # ----- Generic list tabs -----
    def _build_list_tab(self, parent, kind: str):
        # kind in minecraft/java/other
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        # left list, right form
        paned = ttk.PanedWindow(parent, orient="horizontal")
        paned.pack(fill="both", expand=True)
        left = ttk.Frame(paned, padding=4)
        right = ttk.Frame(paned, padding=8)
        paned.add(left, weight=1)
        paned.add(right, weight=2)

        listbox = tk.Listbox(left, font=("Segoe UI", 9))
        listbox.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.configure(yscrollcommand=scrollbar.set)

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Novo", command=lambda: self.list_new(kind)).pack(side="left", padx=2)
        ttk.Button(btns, text="Duplicar", command=lambda: self.list_duplicate(kind)).pack(side="left", padx=2)
        ttk.Button(btns, text="Remover", command=lambda: self.list_remove(kind)).pack(side="left", padx=2)

        # form area - will be populated dynamically
        form_container = ttk.Frame(right)
        form_container.pack(fill="both", expand=True)
        # store refs
        setattr(self, f"{kind}_listbox", listbox)
        setattr(self, f"{kind}_form", form_container)
        setattr(self, f"{kind}_current", None)
        # form fields dict
        setattr(self, f"{kind}_fields", {})

        listbox.bind("<<ListboxSelect>>", lambda e, k=kind: self.list_select(k))
        self._build_form_for_kind(kind, form_container)

    def _build_form_for_kind(self, kind: str, parent):
        # Define fields per kind
        defs = {
            "minecraft": [("id", "ID (ex: 1.8.9)", False), ("name", "Nome", False), ("description", "Descrição", True), ("link", "Link (https://)", False), ("banner", "Banner URL (opcional)", False), ("warning", "Warning (opcional)", True)],
            "java": [("version", "Version (ex: 21)", False), ("name", "Nome", False), ("description", "Descrição", True), ("link", "Link", False)],
            "other": [("name", "Nome", False), ("category", "Categoria (patch/extra/...)", False), ("description", "Descrição", True), ("link", "Link", False), ("banner", "Banner URL", False), ("warning", "Warning", True)],
        }
        fields = {}
        for key, label, is_text in defs[kind]:
            ttk.Label(parent, text=label + ":").pack(anchor="w", pady=(6, 0))
            if is_text:
                txt = tk.Text(parent, height=3, wrap="word", font=("Segoe UI", 9))
                txt.pack(fill="x")
                fields[key] = txt
            else:
                var = tk.StringVar()
                ttk.Entry(parent, textvariable=var).pack(fill="x")
                fields[key] = var
        setattr(self, f"{kind}_fields", fields)
        ttk.Button(parent, text="Aplicar alterações no item selecionado", command=lambda k=kind: self.list_apply(k)).pack(pady=12, fill="x")
        ttk.Label(parent, text="Dica: campos vazios são permitidos (exceto id/nome/version). Link deve ser http/https se preenchido.", font=("Segoe UI", 8), foreground="#666").pack(anchor="w")

    # ----- List operations -----
    def _get_list(self, kind: str) -> list:
        if kind == "minecraft":
            return self.catalog.get("minecraft", {}).get("versions", [])
        return self.catalog.get(kind, [])

    def _set_list(self, kind: str, lst: list):
        if kind == "minecraft":
            if "minecraft" not in self.catalog:
                self.catalog["minecraft"] = {}
            self.catalog["minecraft"]["versions"] = lst
        else:
            self.catalog[kind] = lst

    def list_new(self, kind: str):
        lst = self._get_list(kind)
        template = {
            "minecraft": {"id": "1.21.0", "name": "Minecraft 1.21.0", "description": "", "banner": "", "link": "https://example.com", "warning": ""},
            "java": {"version": "21", "name": "Java 21", "description": "", "link": "https://example.com"},
            "other": {"name": "Novo Recurso", "description": "", "category": "patch", "link": "https://example.com", "banner": "", "warning": ""},
        }[kind]
        lst.append(deepcopy(template))
        self._set_list(kind, lst)
        self.refresh_lists()
        self._mark_dirty()

    def list_duplicate(self, kind: str):
        lb = getattr(self, f"{kind}_listbox")
        sel = lb.curselection()
        if not sel:
            return
        lst = self._get_list(kind)
        lst.append(deepcopy(lst[sel[0]]))
        self.refresh_lists()
        self._mark_dirty()

    def list_remove(self, kind: str):
        lb = getattr(self, f"{kind}_listbox")
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        lst = self._get_list(kind)
        del lst[idx]
        self._set_list(kind, lst)
        self.refresh_lists()
        self._mark_dirty()

    def list_select(self, kind: str):
        lb = getattr(self, f"{kind}_listbox")
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        lst = self._get_list(kind)
        if idx >= len(lst):
            return
        item = lst[idx]
        fields = getattr(self, f"{kind}_fields")
        for key, widget in fields.items():
            val = item.get(key, "")
            if isinstance(widget, tk.Text):
                widget.delete("1.0", "end")
                widget.insert("1.0", val)
            else:
                widget.set(val)
        setattr(self, f"{kind}_current", idx)

    def list_apply(self, kind: str):
        lb = getattr(self, f"{kind}_listbox")
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("Nenhum item", "Selecione um item na lista ou clique em Novo.", parent=self)
            return
        idx = sel[0]
        lst = self._get_list(kind)
        fields = getattr(self, f"{kind}_fields")
        for key, widget in fields.items():
            if isinstance(widget, tk.Text):
                val = widget.get("1.0", "end").strip()
            else:
                val = widget.get().strip()
            lst[idx][key] = val
        self._set_list(kind, lst)
        self.refresh_lists(select_idx=idx)
        self.status.set(f"{kind} [{idx}] atualizado (não esqueça de Salvar).")
        self._mark_dirty()

    # ----- Load/Save -----
    def load_path(self, path: Path):
        try:
            data = load_json(path)
            # validate before accepting
            validate_catalog(data)
            self.catalog = data
            self.current_path = path
            self.path_var.set(str(path))
            self.refresh_all()
            self._snapshot_saved()
            self.status.set(f"Carregado: {path} (v{data.get('app',{}).get('catalog_version','?')})")
        except Exception as e:
            messagebox.showerror("Erro ao carregar", f"{path}\n\n{e}", parent=self)
            self.status.set(f"Falha ao carregar: {e}")

    def refresh_all(self):
        # app tab
        app = self.catalog.get("app", {})
        self.schema_var.set(str(self.catalog.get("schema_version", 1)))
        self.version_var.set(app.get("catalog_version", "1.0.0"))
        self.changelog_text.delete("1.0", "end")
        self.changelog_text.insert("1.0", app.get("changelog", ""))
        launcher = self.catalog.get("launcher", {})
        self.launcher_name_var.set(launcher.get("name", ""))
        self.launcher_link_var.set(launcher.get("link", ""))

        # libs
        libs = self.catalog.get("libraries", {})
        for attr, key in [("libs_name", "name"), ("libs_desc", "description"), ("libs_link", "link"), ("libs_warning", "warning"), ("libs_banner", "banner")]:
            val = libs.get(key, "")
            if hasattr(self, attr + "_text"):
                txt = getattr(self, attr + "_text")
                txt.delete("1.0", "end")
                txt.insert("1.0", val)
            else:
                getattr(self, attr + "_var").set(val)

        self.refresh_lists()
        # raw
        self.raw_text.delete("1.0", "end")
        self.raw_text.insert("1.0", json.dumps(self.catalog, ensure_ascii=False, indent=2))

    def refresh_lists(self, select_idx=None):
        for kind in ("minecraft", "java", "other"):
            lb = getattr(self, f"{kind}_listbox")
            lb.delete(0, "end")
            lst = self._get_list(kind)
            for i, item in enumerate(lst):
                if kind == "minecraft":
                    label = f"{item.get('id','?')} — {item.get('name','')}"
                elif kind == "java":
                    label = f"{item.get('version','?')} — {item.get('name','')}"
                else:
                    label = f"{item.get('name','')} [{item.get('category','')}]"
                lb.insert("end", label)
            if select_idx is not None and 0 <= select_idx < lb.size():
                lb.selection_clear(0, "end")
                lb.selection_set(select_idx)

    def sync_from_ui(self):
        # pull app/libs fields back into catalog
        self.catalog["schema_version"] = 1
        if "app" not in self.catalog:
            self.catalog["app"] = {}
        self.catalog["app"]["catalog_version"] = self.version_var.get().strip() or "1.0.0"
        self.catalog["app"]["changelog"] = self.changelog_text.get("1.0", "end").strip()
        if "launcher" not in self.catalog:
            self.catalog["launcher"] = {}
        self.catalog["launcher"]["name"] = self.launcher_name_var.get().strip()
        self.catalog["launcher"]["link"] = self.launcher_link_var.get().strip()
        # libraries
        libs = self.catalog.get("libraries", {})
        libs["name"] = getattr(self, "libs_name_var").get().strip()
        libs["description"] = getattr(self, "libs_desc_text").get("1.0", "end").strip()
        libs["link"] = getattr(self, "libs_link_var").get().strip()
        libs["warning"] = getattr(self, "libs_warning_text").get("1.0", "end").strip()
        libs["banner"] = getattr(self, "libs_banner_var").get().strip()
        # remove empty banner/warning to keep clean? keep as-is
        self.catalog["libraries"] = libs
        # lists already synced via list_apply, but ensure structure
        if "minecraft" not in self.catalog:
            self.catalog["minecraft"] = {"versions": []}
        if "java" not in self.catalog:
            self.catalog["java"] = []
        if "other" not in self.catalog:
            self.catalog["other"] = []

    def validate(self):
        try:
            self.sync_from_ui()
            # also sync raw if user edited raw but not applied? prioritize UI
            validate_catalog(self.catalog)
            messagebox.showinfo("Válido", "Catálogo válido (schema_version 1). Pronto para hospedar em nuvem.", parent=self)
            self.status.set("Validação OK.")
        except Exception as e:
            messagebox.showerror("Inválido", str(e), parent=self)
            self.status.set(f"Inválido: {e}")

    def save(self) -> bool:
        if not self.current_path:
            return self.save_as()
        self.sync_from_ui()
        try:
            validate_catalog(self.catalog)
        except Exception as e:
            if not messagebox.askyesno("Salvar inválido?", f"Catálogo inválido:\n{e}\n\nSalvar mesmo assim?", parent=self):
                return False
        try:
            save_json(self.current_path, self.catalog)
            self._snapshot_saved()
            self.status.set(f"Salvo: {self.current_path}")
            # tema livre: celebração sutil ao salvar nova versão
            try:
                self._celebrate_save()
            except Exception:
                pass
            messagebox.showinfo("Salvo", f"Arquivo salvo:\n{self.current_path}\n\nFaça upload deste JSON para sua nuvem e atualize a URL no app.", parent=self)
            return True
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e), parent=self)
            return False

    def _celebrate_save(self):
        # confete minimalista no status por 1.5s
        orig = self.status.get()
        self.status.set("✓ Salvo! " + orig)
        self.after(1500, lambda: self.status.set(orig.replace("✓ Salvo! ", "")) if self.status.get().startswith("✓") else None)

    def save_as(self) -> bool:
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".json", filetypes=[("JSON", "*.json")], initialdir=str(PROJECT_ROOT))
        if not path:
            return False
        self.current_path = Path(path)
        self.path_var.set(str(self.current_path))
        return self.save()

    def open_dialog(self):
        if self._is_dirty():
            resp = messagebox.askyesnocancel(
                "Alterações não salvas",
                "Há alterações não salvas. Deseja salvar antes de abrir outro arquivo?",
                parent=self,
            )
            if resp is None:
                return
            if resp and not self.save():
                return
            if resp and self._is_dirty():
                return
        path = filedialog.askopenfilename(parent=self, filetypes=[("JSON", "*.json")], initialdir=str(PROJECT_ROOT))
        if path:
            self.load_path(Path(path))

    def load_from_raw(self):
        try:
            data = json.loads(self.raw_text.get("1.0", "end"))
            validate_catalog(data)
            self.catalog = data
            self.refresh_all()
            self._mark_dirty()
            self.status.set("JSON bruto carregado e válido (não salvo).")
        except Exception as e:
            messagebox.showerror("Erro", f"JSON inválido:\n{e}", parent=self)

def main():
    initial = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if initial and not initial.is_absolute():
        initial = (Path.cwd() / initial).resolve()
    app = CatalogEditor(initial)
    app.mainloop()

if __name__ == "__main__":
    main()
