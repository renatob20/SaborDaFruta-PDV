# ui/bater_ponto_ui.py — PARTE A
"""
UI: Bater Ponto
- Registrar entrada/saída de operadores
- Histórico diário/semanal/mensal
- Export CSV
"""
import os
import sys
import logging
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, filedialog

# garante imports relativos
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.bater_ponto_db import (
    ensure_tables,
    listar_operadores,
    registrar_batida,
    listar_batidas_periodo,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())


class BaterPontoUI(ttk.Toplevel):
    """Janela Toplevel para registro de ponto."""

    def __init__(self, master=None, operador_display=None, role="operador"):
        super().__init__(master=master)
        self.master = master
        self.operador_display = operador_display
        self.role = role

        self.title("⏰ Registro de Ponto")
        self.geometry("950x650")
        self.minsize(800, 500)

        # vars
        self.funcionario_var = StringVar()
        self.periodo_var = StringVar(value="diario")
        self._operadores = []

        # inicializa DB
        try:
            ensure_tables()
        except Exception as e:
            logging.exception("Erro ao inicializar tabelas:")

        # constrói UI
        self._build_ui()
        # carrega dados iniciais
        self._carregar_operadores()
        self._carregar_historico()

    def _build_ui(self):
        """Constrói o layout da janela."""
        pad = 10

        # ===== Frame Top (seleção de operador + botões) =====
        frm_top = ttk.Frame(self)
        frm_top.pack(fill="x", padx=pad, pady=pad)

        ttk.Label(frm_top, text="Operador:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.func_cb = ttk.Combobox(
            frm_top,
            textvariable=self.funcionario_var,
            width=30,
            state="readonly"
        )
        self.func_cb.pack(side="left", padx=(0, 10))

        ttk.Button(
            frm_top,
            text="✅ Registrar Ponto",
            bootstyle=SUCCESS,
            command=self._registrar_ponto
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            frm_top,
            text="🔄 Atualizar",
            bootstyle=INFO,
            command=self._carregar_operadores
        ).pack(side="left", padx=(0, 5))

        # ===== Frame Filtros =====
        frm_filtros = ttk.Frame(self)
        frm_filtros.pack(fill="x", padx=pad, pady=(0, pad))

        ttk.Label(frm_filtros, text="Período:", font=("Arial", 10)).pack(side="left", padx=(0, 5))

        for periodo in ["diario", "semanal", "mensal"]:
            ttk.Radiobutton(
                frm_filtros,
                text=periodo.capitalize(),
                variable=self.periodo_var,
                value=periodo,
                command=self._carregar_historico
            ).pack(side="left", padx=5)

        ttk.Button(
            frm_filtros,
            text="💾 Exportar CSV",
            bootstyle=OUTLINE,
            command=self._exportar_csv
        ).pack(side="right", padx=0)

        # ===== Frame Histórico (Treeview) =====
        frm_hist = ttk.Frame(self)
        frm_hist.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        cols = ("id", "operador", "tipo", "timestamp")
        self.tree = ttk.Treeview(
            frm_hist,
            columns=cols,
            show="headings",
            height=20
        )

        # config colunas
        self.tree.heading("id", text="ID")
        self.tree.heading("operador", text="Operador")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("timestamp", text="Data/Hora")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("operador", width=200, anchor="w")
        self.tree.column("tipo", width=100, anchor="center")
        self.tree.column("timestamp", width=300, anchor="w")

        self.tree.pack(side="left", fill="both", expand=True)

        # scrollbar
        sb = ttk.Scrollbar(frm_hist, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def _carregar_operadores(self):
        """Carrega lista de operadores do banco e popula o Combobox."""
        logging.debug("_carregar_operadores() chamado")
        try:
            self._operadores = listar_operadores()
            logging.debug(f"Carregados {len(self._operadores)} operadores")

            valores = [display for (_id, display, _u) in self._operadores]
            self.func_cb['values'] = valores

            # tenta selecionar o operador passado no construtor
            if self.operador_display and self.operador_display in valores:
                self.funcionario_var.set(self.operador_display)
            elif valores:
                self.funcionario_var.set(valores[0])
        except Exception as e:
            logging.exception("Erro ao carregar operadores:")
            messagebox.showerror("Erro", f"Não foi possível carregar operadores: {e}")

    def _registrar_ponto(self):
        """Registra uma batida (entrada ou saída)."""
        logging.debug("_registrar_ponto() chamado")

        nome_sel = (self.funcionario_var.get() or "").strip()
        if not nome_sel:
            messagebox.showwarning("Atenção", "Selecione um operador.")
            return

        # busca o id do operador
        match = next((op for op in self._operadores if op[1] == nome_sel), None)
        if not match:
            messagebox.showerror("Erro", f"Operador '{nome_sel}' não encontrado.")
            return

        funcionario_id = match[0]
        logging.debug(f"Operador selecionado: id={funcionario_id} nome={nome_sel}")

        # decide tipo (entrada ou saída) alternando a partir do histórico
        try:
            rows = listar_batidas_periodo(periodo="diario", funcionario_id=funcionario_id)
            last = rows[0] if rows else None

            if last and last[2].lower() == "entrada":
                tipo = "saida"
            else:
                tipo = "entrada"

            logging.debug(f"Tipo escolhido: {tipo} (baseado no último: {last[2] if last else 'nenhum'})")
        except Exception as e:
            logging.debug(f"Erro ao determinar tipo: {e} — assumindo 'entrada'")
            tipo = "entrada"

        try:
            bid = registrar_batida(funcionario_id, tipo)
            messagebox.showinfo(
                "Sucesso",
                f"Batida registrada!\n\nOperador: {nome_sel}\nTipo: {tipo.upper()}\nID: {bid}"
            )
            self._carregar_historico()
        except Exception as e:
            logging.exception("Erro ao registrar batida:")
            messagebox.showerror("Erro", f"Falha ao registrar batida: {e}")

    def _carregar_historico(self):
        """Carrega histórico de batidas no Treeview."""
        logging.debug("_carregar_historico() chamado")

        # limpa tree
        for r in self.tree.get_children():
            self.tree.delete(r)

        try:
            periodo = self.periodo_var.get()
            rows = listar_batidas_periodo(periodo=periodo)
            logging.debug(f"Carregadas {len(rows)} batidas para período '{periodo}'")

            for row in rows:
                self.tree.insert("", "end", values=row)
        except Exception as e:
            logging.exception("Erro ao carregar histórico:")
            messagebox.showerror("Erro", f"Não foi possível carregar histórico: {e}")

    def _exportar_csv(self):
        """Exporta histórico para arquivo CSV."""
        logging.debug("_exportar_csv() chamado")

        fn = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*")]
        )

        if not fn:
            return

        try:
            from database.bater_ponto_db import exportar_csv
            exportar_csv(fn)
            messagebox.showinfo("Sucesso", f"Arquivo exportado:\n{fn}")
            logging.debug(f"Arquivo exportado: {fn}")
        except Exception as e:
            logging.exception("Erro ao exportar CSV:")
            messagebox.showerror("Erro", f"Falha ao exportar: {e}")


# Execução direta para teste
if __name__ == "__main__":
    import sys
    
    # obtém argumentos passados via linha de comando (do dashboard)
    operador_display = sys.argv[1] if len(sys.argv) > 1 else "Operador"
    role = sys.argv[2] if len(sys.argv) > 2 else "operador"
    
    # cria janela root (mainloop próprio)
    root = ttk.Window(themename="superhero")
    root.withdraw()  # oculta a root invisível
    
    # cria janela de bater ponto como filha
    win = BaterPontoUI(master=root, operador_display=operador_display, role=role)
    win.transient(root)
    
    def on_close():
        win.destroy()
        root.destroy()
    
    win.protocol("WM_DELETE_WINDOW", on_close)
    root.deiconify()
    root.mainloop()
