# ui/relatorios_ui.py  — PARTE A
"""
UI Relatórios - versão compatível.
Assinatura flexível (operador, role).
"""
import os
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ui/relatorios_ui.py  — PARTE B

class RelatoriosUI(ttk.Window):
    def __init__(self, *args, **kwargs):
        operador = kwargs.pop("operador", None)
        role = kwargs.pop("role", "operador")
        kwargs.pop("master", None)
        super().__init__(themename="superhero")
        self.title("📈 Relatórios")
        self.geometry("900x600")
        self.operador = operador
        self.role = role

        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text="Relatórios", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        ttk.Label(header, text=f"Operador: {self.operador or '—'}").pack(side=RIGHT)

        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # filtros simples
        filters = ttk.Frame(main)
        filters.pack(fill="x", pady=6)
        ttk.Button(filters, text="📄 Relatório Vendas (Exemplo)", bootstyle=PRIMARY, command=self._dummy).pack(side=LEFT)
        ttk.Button(filters, text="📄 Relatório Estoque", bootstyle=SECONDARY, command=self._dummy).pack(side=LEFT, padx=6)
        ttk.Button(filters, text="🔙 Voltar", bootstyle=INFO, command=self._voltar).pack(side=RIGHT)

        # placeholder area
        area = ttk.Labelframe(main, text="Relatório (preview)", padding=8)
        area.pack(fill="both", expand=True, pady=8)
        ttk.Label(area, text="Área de relatórios: implemente filtros e exportadores conforme necessidade.").pack(padx=8, pady=8)

    def _dummy(self):
        messagebox.showinfo("Info", "Funcionalidade de relatório (stub).")

    def _voltar(self):
        try:
            self.destroy()
        except Exception:
            pass

