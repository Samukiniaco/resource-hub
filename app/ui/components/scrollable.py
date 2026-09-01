"""Scrollable frame correto — sem overscroll, scrollbar funcional."""
import tkinter as tk
from tkinter import ttk

from app.ui.styles import COLORS

class ScrollableFrame(ttk.Frame):
    """Frame com Canvas + Scrollbar que não permite overscroll e só mostra barra quando necessário."""
    def __init__(self, parent: tk.Misc, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)

        # Container com borda sutil
        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Modern.Vertical.TScrollbar")
        self.inner = ttk.Frame(self.canvas, style="TFrame")

        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=self._on_scroll)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # eventos
        self.inner.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # mousewheel só quando está sobre o widget
        self.inner.bind("<Enter>", self._bind_wheel)
        self.inner.bind("<Leave>", self._unbind_wheel)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

        # inicia no topo
        self.canvas.yview_moveto(0)

    def _on_scroll(self, first, last):
        # mostra/esconde scrollbar quando necessário
        if float(first) <= 0 and float(last) >= 1:
            self.scrollbar.grid_remove()
        else:
            self.scrollbar.grid()
        self.scrollbar.set(first, last)

    def _update_scrollregion(self, event=None):
        # atualiza scrollregion para exatamente o tamanho do conteúdo — sem padding extra
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # garante que não ficou offset negativo após resize
        first, _ = self.canvas.yview()
        if float(first) < 0:
            self.canvas.yview_moveto(0)

    def _on_canvas_configure(self, event):
        # faz o inner ter a largura do canvas (sem deixar brecha)
        self.canvas.itemconfig(self._window_id, width=event.width)
        # atualiza scrollregion após redimensionar
        self.after_idle(self._update_scrollregion)

    # ---- mousewheel ----
    def _bind_wheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        # Linux
        self.canvas.bind_all("<Button-4>", lambda e: self._on_mousewheel(e), add="+")
        self.canvas.bind_all("<Button-5>", lambda e: self._on_mousewheel(e), add="+")

    def _unbind_wheel(self, event=None):
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        except tk.TclError:
            pass

    def _on_mousewheel(self, event):
        # só rola se houver conteúdo rolável
        first, last = self.canvas.yview()
        if float(first) <= 0 and float(last) >= 1:
            return "break"
        delta = 0
        if hasattr(event, "delta"):
            # Windows: delta múltiplo de 120
            delta = int(-1 * (event.delta / 120))
        elif getattr(event, "num", None) == 4:
            delta = -3
        elif getattr(event, "num", None) == 5:
            delta = 3
        if delta != 0:
            self.canvas.yview_scroll(delta, "units")
        return "break"
