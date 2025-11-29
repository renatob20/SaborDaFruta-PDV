# ui/produtos_ui.py  — PARTE A
"""
UI Produtos - versão compatível.
Aceita assinatura flexível: ProdutosUI(operador=None, role='operador') ou ProdutosUI(master=..., operador=..., role=...)
Foi escrita de forma defensiva para não causar erros de assinatura quando chamada pela dashboard.
"""

import os
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ui/produtos_ui.py  — PARTE B

class ProdutosUI(ttk.Window):
    def __init__(self, *args, **kwargs):
        """
        Compatibilidade:
        - Pode ser chamado como ProdutosUI(operador="Nome", role="admin")
        - Ou ProdutosUI(master=..., operador=..., role=...)
        Então extraímos argumentos conhecidos e inicializamos a janela.
        """
        # extrai argumentos possiveis
        operador = kwargs.pop("operador", kwargs.pop("operador_display", None))
        role = kwargs.pop("role", "operador")
        # aceita master sem quebrar (removemos se presente)
        kwargs.pop("master", None)

        # inicializa como janela ttkbootstrap
        super().__init__(themename="superhero")
        self.title("📦 Produtos - Gestão")
        self.geometry("800x520")
        self.operador = operador
        self.role = role

        # variáveis UI
        self.search_var = StringVar()

        # build UI
        self._build_ui()
        # (carregamentos de dados podem ser ligados aqui)

# ui/produtos_ui.py  — PARTE C

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text="Produtos", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        ttk.Label(header, text=f"Operador: {self.operador or '—'}").pack(side=RIGHT)

        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # search row
        row = ttk.Frame(main)
        row.pack(fill="x", pady=6)
        ttk.Label(row, text="Buscar:").pack(side=LEFT, padx=(0,6))
        ttk.Entry(row, textvariable=self.search_var, width=40).pack(side=LEFT, padx=(0,6))
        ttk.Button(row, text="🔎 Pesquisar", bootstyle=INFO, command=self._dummy_action).pack(side=LEFT)

        # tabela (placeholder)
        table_frame = ttk.Labelframe(main, text="Lista de Produtos", padding=8)
        table_frame.pack(fill="both", expand=True, pady=8)

        cols = ("id", "nome", "tipo", "preco", "estoque")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, anchor="center" if c in ("id","preco","estoque") else "w", width=120)
        self.tree.pack(fill="both", expand=True, side=LEFT)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side=RIGHT, fill="y")

        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="➕ Novo Produto", bootstyle=PRIMARY, command=self._dummy_action).pack(side=LEFT)
        ttk.Button(actions, text="✏️ Editar", bootstyle=SECONDARY, command=self._dummy_action).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="🔙 Voltar", bootstyle=INFO, command=self._voltar).pack(side=RIGHT)

    def _dummy_action(self):
        messagebox.showinfo("Ação", "Funcionalidade ainda não implementada neste stub.")

    def _voltar(self):
        try:
            # se veio de uma dashboard com master, tenta devolver
            self.destroy()
        except Exception:
            try:
                self.quit()
            except Exception:
                pass

