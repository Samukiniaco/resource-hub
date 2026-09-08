"""Editor de tema escondido — cores, light/dark, anime presets, import/export."""
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from pathlib import Path
import json

from app.services.theme_service import (
    PRESETS, DEFAULT_DARK, load_theme, save_theme, reset_theme,
    get_colors, export_theme_file, import_theme_file, THEME_CUSTOM_HEADER
)
from app.ui.styles import apply_theme, COLORS
from app.utils.logger import get_logger

logger = get_logger(__name__)

EDITABLE_KEYS = ["accent", "bg", "bg_top", "bg_card", "border", "text_primary", "warning_bg"]

PRESET_LABELS = {
    "dark": "Dark (padrão)",
    "light": "Light",
    "kobayashi": "Kobayashi Dragon Maid 🌿",
    "nichijou": "Nichijou ☀️",
    "azumanga": "Azumanga Daioh 🌸",
    "k_on": "K-On! 🎸",
    "bocchi": "Bocchi the Rock! 🎧",
    "minecraft": "Minecraft ⛏️",
}

def open_theme_editor(parent: tk.Tk, on_apply=None):
    dlg = tk.Toplevel(parent)
    dlg.title("Tema — Editor escondido")
    dlg.transient(parent)
    dlg.grab_set()
    dlg.geometry("520x640")
    dlg.minsize(480, 560)
    dlg.configure(bg=COLORS["bg"])

    # estado
    current = load_theme()
    selected_mode = tk.StringVar(value=current.get("mode", "dark"))
    # preview colors (não salvo até Aplicar)
    preview_colors = dict(get_colors())

    header = tk.Frame(dlg, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    header.pack(fill="x", padx=12, pady=12)
    h = tk.Frame(header, bg=COLORS["bg_card"])
    h.pack(fill="x", padx=14, pady=10)
    tk.Label(h, text="✦ Editor de Tema", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
    tk.Label(h, text="Escondido — 7 cliques no logo. Mude cores, light/dark e imagens. Exporte .rhtheme para compartilhar.", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=("Segoe UI", 8), wraplength=460, justify="left").pack(anchor="w", pady=(4, 0))

    # Presets
    preset_frame = ttk.LabelFrame(dlg, text="Presets (anime light + dark)", padding=8)
    preset_frame.pack(fill="x", padx=12, pady=(0, 8))
    cb = ttk.Combobox(preset_frame, values=[f"{k} — {PRESET_LABELS.get(k,k)}" for k in PRESETS.keys()], state="readonly", width=40)
    # seleciona atual
    try:
        idx = list(PRESETS.keys()).index(selected_mode.get())
        cb.current(idx)
    except ValueError:
        cb.set(f"{selected_mode.get()} — custom")
    cb.pack(fill="x")
    info = tk.Label(preset_frame, text="Presets são só cores — leves, sem baixar imagens. Depois você pode baixar temas completos ou importar .rhtheme.", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7), wraplength=460, justify="left")
    info.pack(anchor="w", pady=(6, 0))

    # Cores editáveis
    colors_frame = ttk.LabelFrame(dlg, text="Cores (clique para escolher)", padding=8)
    colors_frame.pack(fill="x", padx=12, pady=4)
    btns = {}
    def _refresh_preview():
        apply_theme(parent, override=preview_colors)
        # atualiza botões
        for k, btn in btns.items():
            btn.configure(bg=preview_colors.get(k, "#000"))

    def _pick_color(key):
        initial = preview_colors.get(key, "#000000")
        color = colorchooser.askcolor(initialcolor=initial, title=f"Escolher {key}", parent=dlg)
        if color and color[1]:
            preview_colors[key] = color[1].lower()
            _refresh_preview()
            selected_mode.set("custom")
            cb.set("custom — personalizado")

    for key in EDITABLE_KEYS:
        row = tk.Frame(colors_frame, bg=dlg.cget("bg"))
        row.pack(fill="x", pady=2)
        tk.Label(row, text=key, bg=dlg.cget("bg"), fg=COLORS["text_secondary"], font=("Segoe UI", 8), width=14, anchor="w").pack(side="left")
        b = tk.Button(row, bg=preview_colors.get(key, "#000"), width=4, relief="flat", bd=1, highlightthickness=0,
                      command=lambda k=key: _pick_color(k), cursor="hand2")
        b.pack(side="left", padx=6)
        tk.Label(row, text=preview_colors.get(key, ""), bg=dlg.cget("bg"), fg=COLORS["text_muted"], font=("Consolas", 7)).pack(side="left")

    # Imagens
    img_frame = ttk.LabelFrame(dlg, text="Imagens (opcional)", padding=8)
    img_frame.pack(fill="x", padx=12, pady=4)
    tk.Label(img_frame, text="Header custom: data/header_bg.custom.png — use PNG/JPG 1020×88. Vazio = cor sólida.", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7), wraplength=460, justify="left").pack(anchor="w")
    img_row = tk.Frame(img_frame, bg=dlg.cget("bg"))
    img_row.pack(fill="x", pady=4)
    def _choose_header():
        p = filedialog.askopenfilename(parent=dlg, title="Escolher header", filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")])
        if not p:
            return
        try:
            from PIL import Image
            im = Image.open(p)
            im.thumbnail((1020, 88), Image.LANCZOS)
            # salva como custom
            THEME_CUSTOM_HEADER.parent.mkdir(parents=True, exist_ok=True)
            im.save(THEME_CUSTOM_HEADER, format="PNG")
            messagebox.showinfo("Header", f"Header salvo em {THEME_CUSTOM_HEADER}\nReinicie o app para ver (ou Aplicar tema).", parent=dlg)
        except Exception as e:
            # fallback cópia bruta
            try:
                import shutil
                shutil.copy(p, THEME_CUSTOM_HEADER)
                messagebox.showinfo("Header", f"Copiado para {THEME_CUSTOM_HEADER}", parent=dlg)
            except Exception as e2:
                messagebox.showerror("Erro", str(e2), parent=dlg)
    ttk.Button(img_row, text="Escolher header…", command=_choose_header).pack(side="left")
    def _clear_header():
        try:
            THEME_CUSTOM_HEADER.unlink(missing_ok=True)
            messagebox.showinfo("Header", "Removido. Voltará à cor sólida.", parent=dlg)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=dlg)
    ttk.Button(img_row, text="Remover", command=_clear_header).pack(side="left", padx=6)
    if THEME_CUSTOM_HEADER.exists():
        tk.Label(img_frame, text=f"✔ custom header existe ({THEME_CUSTOM_HEADER.stat().st_size} bytes)", bg=dlg.cget("bg"), fg=COLORS["success"], font=("Segoe UI", 7)).pack(anchor="w")

    # Import/Export
    io_frame = ttk.LabelFrame(dlg, text="Temas compartilháveis (.rhtheme)", padding=8)
    io_frame.pack(fill="x", padx=12, pady=4)
    tk.Label(io_frame, text="Exporte seu tema e envie para amigos. Eles importam e aplicam. Também dá para baixar temas da comunidade via catálogo futuro.", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7), wraplength=460, justify="left").pack(anchor="w")
    io_row = tk.Frame(io_frame, bg=dlg.cget("bg"))
    io_row.pack(fill="x", pady=4)
    def _export():
        p = filedialog.asksaveasfilename(parent=dlg, title="Exportar tema", defaultextension=".rhtheme", filetypes=[("Tema", "*.rhtheme"), ("JSON", "*.json")], initialfile="meu-tema.rhtheme")
        if not p:
            return
        try:
            # salva preview atual temporariamente para exportar
            from app.services.theme_service import save_theme as _save, get_colors as _get
            # export usa cores preview
            tmp_path = Path(p)
            payload = {"format": "rhtheme", "version": 1, "mode": selected_mode.get(), "colors": dict(preview_colors), "meta": {"exported_from": "Resource Hub"}}
            tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("Exportado", f"Salvo em {tmp_path}\nEnvie este arquivo para aplicar em outro PC via Importar.", parent=dlg)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=dlg)
    def _import():
        p = filedialog.askopenfilename(parent=dlg, title="Importar tema", filetypes=[("Tema", "*.rhtheme *.json"), ("Todos", "*.*")])
        if not p:
            return
        try:
            import_theme_file(Path(p))
            # recarrega
            new_colors = get_colors()
            preview_colors.clear()
            preview_colors.update(new_colors)
            _refresh_preview()
            # atualiza combobox
            info2 = load_theme()
            selected_mode.set(info2.get("mode", "custom"))
            messagebox.showinfo("Importado", f"Tema importado de {p}\nClique Aplicar para persistir e ver no app.", parent=dlg)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=dlg)
    ttk.Button(io_row, text="Exportar .rhtheme…", command=_export).pack(side="left")
    ttk.Button(io_row, text="Importar…", command=_import).pack(side="left", padx=6)

    def _on_preset(e=None):
        txt = cb.get()
        key = txt.split(" —")[0].strip() if " —" in txt else txt.strip()
        if key in PRESETS:
            selected_mode.set(key)
            preview_colors.clear()
            preview_colors.update(PRESETS[key])
            _refresh_preview()
    cb.bind("<<ComboboxSelected>>", _on_preset)

    # Botões finais
    btns = tk.Frame(dlg, bg=dlg.cget("bg"))
    btns.pack(fill="x", padx=12, pady=12)
    def _apply():
        # persiste
        save_theme(selected_mode.get(), {k: preview_colors[k] for k in EDITABLE_KEYS if k in preview_colors})
        apply_theme(parent)
        try:
            # reconstrói tabs se possível
            if hasattr(parent, "winfo_children"):
                # procura MainWindow via parent
                pass
        except Exception:
            pass
        if on_apply:
            try:
                on_apply()
            except Exception:
                pass
        dlg.destroy()
        messagebox.showinfo("Tema", "Tema aplicado e salvo em data/theme.json (local, não vai pro GitHub). Reinicie se algo não atualizar.", parent=parent)
    def _reset():
        reset_theme()
        preview_colors.clear()
        preview_colors.update(PRESETS["dark"])
        selected_mode.set("dark")
        apply_theme(parent, override=PRESETS["dark"])
        # não salva até Aplicar — preview
    def _cancel():
        # restaura tema salvo (descarta preview)
        apply_theme(parent)
        dlg.destroy()

    ttk.Button(btns, text="Cancelar", command=_cancel).pack(side="right", padx=4)
    ttk.Button(btns, text="Resetar padrão", command=_reset).pack(side="right", padx=4)
    ttk.Button(btns, text="Aplicar", style="Accent.TButton", command=_apply).pack(side="right", padx=4)

    dlg.bind("<Escape>", lambda e: _cancel())
