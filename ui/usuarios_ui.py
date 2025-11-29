# ui/usuarios_ui.py  — PARTE A
"""
UI Usuários - versão compatível com Dashboard.
Assinatura de construtor é flexível (aceita operador e role).
"""
import os
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ui/usuarios_ui.py  — PARTE B

class UsuariosUI(ttk.Window):
    def __init__(self, *args, **kwargs):
        operador = kwargs.pop("operador", None)
        role = kwargs.pop("role", "operador")
        kwargs.pop("master", None)  # não usamos master diretamente
        super().__init__(themename="superhero")
        self.title("👤 Usuários - Gestão")
        self.geometry("780x520")
        self.operador = operador
        self.role = role

        # UI vars
        self.filter_var = StringVar()

        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text="Usuários", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        ttk.Label(header, text=f"Operador: {self.operador or '—'}").pack(side=RIGHT)

        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x", pady=6)
        ttk.Label(top, text="Filtrar:").pack(side=LEFT)
        ttk.Entry(top, textvariable=self.filter_var, width=40).pack(side=LEFT, padx=6)
        ttk.Button(top, text="🔎 Filtrar", command=self._dummy).pack(side=LEFT)

        table = ttk.Labelframe(main, text="Lista de Usuários", padding=8)
        table.pack(fill="both", expand=True)
        cols = ("id", "nome", "role", "ativo")
        self.tree = ttk.Treeview(table, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, anchor="center", width=120)
        self.tree.pack(fill="both", expand=True, side=LEFT)
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side=RIGHT, fill="y")

        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="➕ Novo", bootstyle=PRIMARY, command=self._dummy).pack(side=LEFT)
        ttk.Button(actions, text="✏️ Editar", bootstyle=SECONDARY, command=self._dummy).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="🔙 Voltar", bootstyle=INFO, command=self._voltar).pack(side=RIGHT)

    def _dummy(self):
        messagebox.showinfo("Info", "Funcionalidade não implementada no stub.")

    def _voltar(self):
        try:
            self.destroy()
        except Exception:
            pass

