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
    "sakura": "Sakura 🌸 Light",
    "sakura_dark": "Sakura 🌸 Dark",
    "ocean": "Ocean 🌊 Light",
    "ocean_dark": "Ocean 🌊 Dark",
    "forest": "Forest 🌿 Light",
    "forest_dark": "Forest 🌿 Dark",
    "sunset": "Sunset ☀️ Light",
    "sunset_dark": "Sunset ☀️ Dark",
    "grape": "Grape 🍇 Light",
    "grape_dark": "Grape 🍇 Dark",
    "ember": "Ember 🔥 Light",
    "ember_dark": "Ember 🔥 Dark",
    "minecraft": "Minecraft ⛏️ Dark",
    "minecraft_light": "Minecraft ⛏️ Light",
}

def open_theme_editor(parent: tk.Tk, on_apply=None):
    dlg = tk.Toplevel(parent)
    dlg.title("Tema — Editor escondido")
    dlg.transient(parent)
    dlg.grab_set()
    dlg.geometry("520x640")
    dlg.minsize(480, 560)
    dlg.configure(bg=COLORS["bg"])
    dlg.geometry("560x700")

    # estado
    current = load_theme()
    selected_mode = tk.StringVar(value=current.get("mode", "dark"))
    preview_colors = dict(get_colors())

    # scroll para caber carrossel + tudo
    from app.ui.components.scrollable import ScrollableFrame
    outer = ttk.Frame(dlg)
    outer.pack(fill="both", expand=True)
    sc = ScrollableFrame(outer)
    sc.pack(fill="both", expand=True, padx=1, pady=1)
    inner = sc.inner

    header = tk.Frame(inner, bg=COLORS["bg_card"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
    header.pack(fill="x", padx=12, pady=12)
    h = tk.Frame(header, bg=COLORS["bg_card"])
    h.pack(fill="x", padx=14, pady=10)
    tk.Label(h, text="✦ Editor de Tema", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
    tk.Label(h, text="Escondido — 7 cliques no logo. Mude cores, light/dark e imagens. Exporte .rhtheme para compartilhar.", bg=COLORS["bg_card"], fg=COLORS["text_muted"], font=("Segoe UI", 8), wraplength=460, justify="left").pack(anchor="w", pady=(4, 0))

    # Presets
    preset_frame = ttk.LabelFrame(inner, text="Presets (anime light + dark)", padding=8)
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
    colors_frame = ttk.LabelFrame(inner, text="Cores (clique para escolher)", padding=8)
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

    # Banners: tamanho + enquadramento + modo (automático p/ todos, sem distorcer)
    banner_frame = ttk.LabelFrame(inner, text="Banners — tamanho e corte (vale p/ todos)", padding=8)
    banner_frame.pack(fill="x", padx=12, pady=4)
    tk.Label(banner_frame, text="Blur = sem cortar cabeças (fundo desfocado). Cover = preenche cortando. Contain = tudo visível com faixas.", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7), wraplength=460, justify="left").pack(anchor="w")
    try:
        from app.services.image_service import get_banner_settings as _get_bs
        _bs0 = _get_bs()
    except Exception:
        _bs0 = {"fit": "blur", "focal": "top", "height": 200}
    banner_fit_var = tk.StringVar(value=_bs0.get("fit", "blur"))
    banner_focal_var = tk.StringVar(value=_bs0.get("focal", "top"))
    banner_height_var = tk.IntVar(value=int(_bs0.get("height", 200)))
    brow = tk.Frame(banner_frame, bg=dlg.cget("bg"))
    brow.pack(fill="x", pady=4)
    tk.Label(brow, text="Modo:", bg=dlg.cget("bg"), fg=COLORS["text_secondary"], font=("Segoe UI", 8)).pack(side="left")
    fit_cb = ttk.Combobox(brow, textvariable=banner_fit_var, values=["blur", "cover", "contain"], state="readonly", width=10, font=("Segoe UI", 8))
    fit_cb.pack(side="left", padx=4)
    tk.Label(brow, text="Foco:", bg=dlg.cget("bg"), fg=COLORS["text_secondary"], font=("Segoe UI", 8)).pack(side="left", padx=(8, 0))
    focal_cb = ttk.Combobox(brow, textvariable=banner_focal_var, values=["top", "center", "bottom"], state="readonly", width=10, font=("Segoe UI", 8))
    focal_cb.pack(side="left", padx=4)
    tk.Label(brow, text="Altura:", bg=dlg.cget("bg"), fg=COLORS["text_secondary"], font=("Segoe UI", 8)).pack(side="left", padx=(8, 0))
    height_scale = tk.Scale(brow, from_=140, to=260, orient="horizontal", variable=banner_height_var, bg=dlg.cget("bg"), fg=COLORS["text_secondary"], highlightthickness=0, length=140, font=("Segoe UI", 7))
    height_scale.pack(side="left", padx=4)
    height_lbl = tk.Label(brow, text=f"{banner_height_var.get()}px", bg=dlg.cget("bg"), fg=COLORS["text_muted"], font=("Segoe UI", 7), width=6)
    height_lbl.pack(side="left")
    def _upd_height_lbl(*a):
        try:
            height_lbl.configure(text=f"{banner_height_var.get()}px")
        except Exception:
            pass
    try:
        banner_height_var.trace_add("write", _upd_height_lbl)
    except Exception:
        pass

    # Cor a partir de imagem (sem header fantasma — header nunca aparecia no app)
    color_img_frame = ttk.LabelFrame(inner, text="Cor a partir de imagem", padding=8)
    color_img_frame.pack(fill="x", padx=12, pady=4)
    tk.Label(color_img_frame, text="Escolha qualquer imagem e puxe a cor dominante para o accent. Combine com seus banners do carrossel.", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7), wraplength=460, justify="left").pack(anchor="w")
    ci_row = tk.Frame(color_img_frame, bg=dlg.cget("bg"))
    ci_row.pack(fill="x", pady=4)
    def _pick_color_from_image():
        p = filedialog.askopenfilename(parent=dlg, title="Escolher imagem", filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")])
        if not p:
            return
        try:
            from pathlib import Path as _P
            from app.services.theme_service import extract_dominant_color
            dom = extract_dominant_color(_P(p))
            if dom:
                preview_colors["accent"] = dom
                _refresh_preview()
                selected_mode.set("custom")
                cb.set("custom — personalizado")
                messagebox.showinfo("Cor", f"Cor dominante {dom} aplicada ao accent (preview). Clique Aplicar.", parent=dlg)
            else:
                messagebox.showwarning("Falha", "Não foi possível extrair cor.", parent=dlg)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=dlg)
    ttk.Button(ci_row, text="Puxar cor de imagem…", command=_pick_color_from_image).pack(side="left")

    # Carrossel de banners (até 15, random sem repetir seguida)
    carousel_frame = ttk.LabelFrame(inner, text="Carrossel de Banners — até 15 imagens (aleatório sem repetir)", padding=8)
    carousel_frame.pack(fill="x", padx=12, pady=4)
    tk.Label(carousel_frame, text="Cada card sem banner no catálogo puxa uma imagem aleatória deste carrossel. Busca auto-preenche com tema, mas pode mudar.", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7), wraplength=460, justify="left").pack(anchor="w")
    # busca
    search_row = tk.Frame(carousel_frame, bg=dlg.cget("bg"))
    search_row.pack(fill="x", pady=4)
    tk.Label(search_row, text="Buscar:", bg=dlg.cget("bg"), fg=COLORS["text_secondary"], font=("Segoe UI", 8)).pack(side="left")
    # auto-preenche com nome do preset
    _preset_queries = {"kobayashi": "maid", "kobayashi_dark": "maid dark", "nichijou": "school_uniform", "nichijou_dark": "school_uniform dark", "azumanga": "azumanga_daioh", "azumanga_dark": "azumanga_daioh dark", "k_on": "school_uniform", "k_on_dark": "school_uniform dark", "bocchi": "school_uniform", "bocchi_dark": "school_uniform dark", "minecraft": "anime", "minecraft_light": "anime light", "dark": "anime", "light": "anime"}
    carousel_search_var = tk.StringVar(value=_preset_queries.get(selected_mode.get(), "anime"))
    carousel_entry = ttk.Entry(search_row, textvariable=carousel_search_var, width=24, font=("Segoe UI", 8))
    carousel_entry.pack(side="left", padx=4, fill="x", expand=True)
    def _on_preset_for_search(*args):
        q = _preset_queries.get(selected_mode.get(), selected_mode.get())
        carousel_search_var.set(q)
    # atualiza busca quando preset muda
    selected_mode.trace_add("write", lambda *_: _on_preset_for_search())

    results_row = tk.Frame(carousel_frame, bg=dlg.cget("bg"))
    results_row.pack(fill="x", pady=4)
    # container para previews da busca
    previews_frame = tk.Frame(carousel_frame, bg=dlg.cget("bg"))
    previews_frame.pack(fill="x", pady=2)

    # lista atual
    current_label = tk.Label(carousel_frame, text="", bg=dlg.cget("bg"), fg=COLORS["text_muted"], font=("Segoe UI", 7))
    current_label.pack(anchor="w")
    current_list_frame = tk.Frame(carousel_frame, bg=dlg.cget("bg"))
    current_list_frame.pack(fill="x", pady=2)

    def _refresh_current_list():
        for w in current_list_frame.winfo_children():
            w.destroy()
        try:
            from app.services.banner_carousel import load_carousel
            lst = load_carousel()
            current_label.configure(text=f"Carrossel atual: {len(lst)}/15 imagens")
            if not lst:
                tk.Label(current_list_frame, text="Vazio — use Busca ou adicione manual.", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7)).pack(anchor="w")
                return
            for idx, url in enumerate(lst):
                row = tk.Frame(current_list_frame, bg=dlg.cget("bg"), highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
                row.pack(fill="x", pady=1)
                # mini preview
                thumb = tk.Label(row, bg=dlg.cget("bg"), width=12, height=4, text="…", font=("Segoe UI", 6))
                thumb.pack(side="left", padx=4, pady=2)
                # fetch thumb async
                try:
                    from app.services.image_service import fetch_image_async
                    def _make_cb(lbl=thumb, u=url):
                        def _cb(img):
                            def _apply():
                                try:
                                    if img:
                                        lbl.configure(image=img, text="", width=220, height=62)
                                        lbl.image = img
                                    else:
                                        lbl.configure(text="×")
                                except tk.TclError:
                                    pass
                            try:
                                dlg.after(0, _apply)
                            except tk.TclError:
                                pass
                        return _cb
                    fetch_image_async(url, _make_cb(), max_size=(220, 62))
                except Exception:
                    pass
                tk.Label(row, text=url[:48] + ("…" if len(url)>48 else ""), bg=dlg.cget("bg"), fg=COLORS["text_secondary"], font=("Consolas", 6), anchor="w").pack(side="left", fill="x", expand=True)
                ttk.Button(row, text="✕", width=3, command=lambda u=url: (_remove_carousel(u), _refresh_current_list())).pack(side="right", padx=2)
        except Exception as e:
            current_label.configure(text=f"Erro: {e}")

    def _remove_carousel(url):
        try:
            from app.services.banner_carousel import remove_from_carousel
            remove_from_carousel(url)
        except Exception:
            pass

    def _render_results(items):
        for w in previews_frame.winfo_children():
            w.destroy()
        if not items:
            tk.Label(previews_frame, text="Nada encontrado — tente 'maid', 'school_uniform' ou cole URL do Google Imagens abaixo.", bg=dlg.cget("bg"), fg=COLORS["text_muted"], font=("Segoe UI", 7), wraplength=440, justify="left").pack(anchor="w")
            return
        for it in items:
            url = it["url"] if isinstance(it, dict) else it
            dom = it.get("dominant", "") if isinstance(it, dict) else ""
            src = it.get("source", "") if isinstance(it, dict) else ""
            row = tk.Frame(previews_frame, bg=dlg.cget("bg"), highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
            row.pack(fill="x", pady=2)
            thumb = tk.Label(row, bg=dlg.cget("bg"), width=12, height=4, text="…", font=("Segoe UI", 6))
            thumb.pack(side="left", padx=4, pady=2)
            try:
                from app.services.image_service import fetch_image_async
                def _make_cb2(lbl=thumb, u=url):
                    def _cb(img):
                        def _apply():
                            try:
                                if img:
                                    lbl.configure(image=img, text="", width=220, height=62)
                                    lbl.image = img
                            except tk.TclError:
                                pass
                        try:
                            dlg.after(0, _apply)
                        except tk.TclError:
                            pass
                    return _cb
                fetch_image_async(url, _make_cb2(), max_size=(220, 62))
            except Exception:
                pass
            mid = tk.Frame(row, bg=dlg.cget("bg"))
            mid.pack(side="left", fill="x", expand=True)
            tk.Label(mid, text=url[:52] + "…", bg=dlg.cget("bg"), fg=COLORS["text_secondary"], font=("Consolas", 6), anchor="w").pack(anchor="w")
            sub = f"{src} {dom}".strip()
            if sub:
                lr = tk.Frame(mid, bg=dlg.cget("bg"))
                lr.pack(anchor="w")
                if dom:
                    tk.Label(lr, text="  ", bg=dom, width=2, font=("Segoe UI", 6)).pack(side="left", padx=(0, 4))
                tk.Label(lr, text=sub, bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 6)).pack(side="left")
            def _add(u=url):
                from app.services.banner_carousel import load_carousel as _lc
                if len(_lc()) >= 15:
                    messagebox.showwarning("Limite", "Máximo 15 imagens no carrossel.", parent=dlg)
                    return
                from app.services.banner_carousel import add_to_carousel as _add
                ok = _add(u)
                if ok:
                    _refresh_current_list()
                else:
                    messagebox.showinfo("Já existe", "Imagem já no carrossel.", parent=dlg)
            ttk.Button(row, text="＋ Adicionar", width=10, command=_add).pack(side="right", padx=4)

    search_state = {"items": [], "page": 0, "per": 6}
    def _render_page():
        start = search_state["page"] * search_state["per"]
        _render_results(search_state["items"][start:start + search_state["per"]])
        total = max(1, (len(search_state["items"]) + search_state["per"] - 1) // search_state["per"])
        page_lbl.configure(text=f"Página {search_state['page']+1}/{total} — {len(search_state['items'])} resultados")
        prev_btn.configure(state="normal" if search_state["page"] > 0 else "disabled")
        next_btn.configure(state="normal" if (search_state["page"]+1) * search_state["per"] < len(search_state["items"]) else "disabled")

    def _do_search():
        import threading
        q = carousel_search_var.get().strip() or "anime"
        for w in previews_frame.winfo_children():
            w.destroy()
        tk.Label(previews_frame, text=f"Buscando '{q}' em NekosAPI + Safebooru (30)…", bg=dlg.cget("bg"), fg=COLORS["text_muted"], font=("Segoe UI", 7)).pack(anchor="w")
        search_btn.configure(state="disabled")
        def _work():
            try:
                from app.services.banner_carousel import search_image_detailed
                items = search_image_detailed(q, count=30)
            except Exception:
                items = []
            def _ui():
                try:
                    search_btn.configure(state="normal")
                except Exception:
                    pass
                if not items:
                    for w in previews_frame.winfo_children():
                        w.destroy()
                    tk.Label(previews_frame, text="Nada encontrado — tente 'maid' ou cole URL manual abaixo.", bg=dlg.cget("bg"), fg=COLORS["text_muted"], font=("Segoe UI", 7), wraplength=440).pack(anchor="w")
                    page_lbl.configure(text="0 resultados")
                    return
                search_state["items"] = items
                search_state["page"] = 0
                _render_page()
            try:
                dlg.after(0, _ui)
            except tk.TclError:
                pass
        threading.Thread(target=_work, daemon=True).start()

    search_btn = ttk.Button(search_row, text="Buscar", width=8, command=_do_search)
    search_btn.pack(side="left", padx=4)
    page_lbl = tk.Label(search_row, text="", bg=dlg.cget("bg"), fg=COLORS["text_muted"], font=("Segoe UI", 7))
    page_lbl.pack(side="left", padx=4)
    prev_btn = ttk.Button(search_row, text="◀", width=3, command=lambda: (search_state.__setitem__("page", max(0, search_state["page"]-1)), _render_page()))
    prev_btn.pack(side="left")
    next_btn = ttk.Button(search_row, text="▶", width=3, command=lambda: (search_state.__setitem__("page", search_state["page"]+1), _render_page()))
    next_btn.pack(side="left", padx=2)
    def _clear_search():
        for w in previews_frame.winfo_children():
            w.destroy()
    ttk.Button(search_row, text="Limpar", width=6, command=_clear_search).pack(side="left")
    def _clear_carousel():
        if messagebox.askyesno("Limpar", "Remover todas as 15 imagens do carrossel?", parent=dlg):
            try:
                from app.services.banner_carousel import save_carousel
                save_carousel([])
                _refresh_current_list()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=dlg)
    ttk.Button(search_row, text="Esvaziar", width=8, command=_clear_carousel).pack(side="left", padx=2)

    # Manual — Google Imagens sem API: cole o endereço aqui
    manual_row = tk.Frame(carousel_frame, bg=dlg.cget("bg"))
    manual_row.pack(fill="x", pady=4)
    tk.Label(manual_row, text="URL manual (Google Imagens → botão direito → copiar endereço):", bg=dlg.cget("bg"), fg=COLORS["text_dim"], font=("Segoe UI", 7)).pack(anchor="w")
    manual_var = tk.StringVar()
    manual_entry = ttk.Entry(manual_row, textvariable=manual_var, font=("Segoe UI", 7))
    manual_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
    def _add_manual():
        u = manual_var.get().strip()
        if not u.startswith("http"):
            messagebox.showwarning("URL inválida", "Cole uma URL http(s) direta de imagem (Google → copiar endereço da imagem).", parent=dlg)
            return
        from app.services.banner_carousel import load_carousel as _lc, add_to_carousel as _ad
        if len(_lc()) >= 15:
            messagebox.showwarning("Limite", "Máximo 15 imagens.", parent=dlg)
            return
        if _ad(u):
            manual_var.set("")
            _refresh_current_list()
        else:
            messagebox.showinfo("Já existe", "Imagem já no carrossel.", parent=dlg)
    ttk.Button(manual_row, text="＋ Adicionar URL", width=14, command=_add_manual).pack(side="left")

    _refresh_current_list()

    # Import/Export
    io_frame = ttk.LabelFrame(inner, text="Temas compartilháveis (.rhtheme)", padding=8)
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
        # persiste TODAS as cores do preview + banner settings
        from app.services.theme_service import DEFAULT_DARK as _DD, HEX_RE as _HEX
        full = {k: v for k, v in preview_colors.items() if k in _DD and isinstance(v, str) and _HEX.match(v.strip())}
        save_theme(selected_mode.get(), full)
        try:
            import json
            from app.config import DATA_DIR as _DD2
            _tp = _DD2 / "theme.json"
            _cur = json.loads(_tp.read_text(encoding="utf-8")) if _tp.exists() else {}
            _cur["banner_fit"] = banner_fit_var.get().strip()
            _cur["banner_focal"] = banner_focal_var.get().strip()
            _cur["banner_height"] = int(banner_height_var.get())
            _tp.write_text(json.dumps(_cur, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass
        # limpa cache de banners para o novo tamanho/modo valer na hora
        try:
            from app.services import image_service as _is
            _is._photo_cache.clear()
        except Exception:
            pass
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
