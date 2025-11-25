# ui/bater_ponto_ui.py
"""
UI moderna para Bater Ponto (TTkBootstrap).
Botão único "Registrar Ponto" que alterna Entrada / Saída automaticamente
com base na contagem de batidas do dia (par/ímpar).
Admin tem botão "Ajustar Ponto".
"""

import os
import sys
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar
from tkinter.filedialog import asksaveasfilename
from datetime import datetime

# assegura path do projeto para imports relativos funcionarem
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# importa funções do DB
from database.bater_ponto_db import (
    ensure_tables,
    listar_operadores,
    contar_batidas_dia,
    registrar_batida,
    listar_batidas_periodo,
    exportar_csv
)

class BaterPontoUI(ttk.Window):
    def __init__(self, master=None, operador_display=None, role="operador"):
        # cria janela com tema padronizado
        super().__init__(themename="superhero")
        self.master = master
        self.operador_display = operador_display
        self.role = role

        self.title("⏰ Registro de Ponto")
        self.geometry("900x600")
        self.minsize(900,600)

        # garante tabela
        ensure_tables()

        # vars
        self.funcionario_var = StringVar()
        self.periodo_var = StringVar(value="diario")  # diario/semanal/mensal

        # contrói UI
        self._build_ui()
        # carrega dados
        self._carregar_operadores()
        self._carregar_historico()

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill=X)
        ttk.Label(header, text="Registro de Ponto", font=("Segoe UI", 18, "bold")).pack(side=LEFT)
        ttk.Label(header, text=f"Operador: {self.operador_display or '—'}", font=("Segoe UI", 10)).pack(side=RIGHT)

        main = ttk.Frame(self, padding=10)
        main.pack(fill=BOTH, expand=True)

        # Seleção funcionário
        sel = ttk.Labelframe(main, text="Funcionário", padding=10)
        sel.pack(fill=X, pady=8)

        ttk.Label(sel, text="Funcionário:").grid(row=0, column=0, padx=6, pady=6, sticky=W)
        self.combo_func = ttk.Combobox(sel, textvariable=self.funcionario_var, state="readonly", width=40)
        self.combo_func.grid(row=0, column=1, padx=6, pady=6, sticky=W)

        # Botão único: Registrar Ponto
        ttk.Button(sel, text="⏺️ Registrar Ponto", bootstyle=SUCCESS, command=self._registrar_ponto)\
            .grid(row=0, column=2, padx=10)

        # Admin: ajuste de ponto (visível só para admin)
        if (self.role or "").lower() == "admin":
            ttk.Button(sel, text="🔧 Ajustar Ponto", bootstyle=INFO, command=self._ajustar_ponto)\
                .grid(row=0, column=3, padx=6)

        # Período
        filtro = ttk.Labelframe(main, text="Período", padding=8)
        filtro.pack(fill=X, pady=6)
        ttk.Radiobutton(filtro, text="Diário", value="diario", variable=self.periodo_var, command=self._carregar_historico).pack(side=LEFT, padx=10)
        ttk.Radiobutton(filtro, text="Semanal", value="semanal", variable=self.periodo_var, command=self._carregar_historico).pack(side=LEFT, padx=10)
        ttk.Radiobutton(filtro, text="Mensal", value="mensal", variable=self.periodo_var, command=self._carregar_historico).pack(side=LEFT, padx=10)

        # Histórico
        hist = ttk.Labelframe(main, text="Histórico de Batidas", padding=8)
        hist.pack(fill=BOTH, expand=True, pady=(8,0))

        cols = ("id", "func", "tipo", "timestamp")
        self.tree = ttk.Treeview(hist, columns=cols, show="headings")
        self.tree.heading("id", text="ID"); self.tree.column("id", width=60, anchor="center")
        self.tree.heading("func", text="Funcionário"); self.tree.column("func", width=220)
        self.tree.heading("tipo", text="Batida"); self.tree.column("tipo", width=120, anchor="center")
        self.tree.heading("timestamp", text="Data/Hora"); self.tree.column("timestamp", width=180, anchor="center")
        self.tree.pack(fill=BOTH, expand=True, side=LEFT)

        vsb = ttk.Scrollbar(hist, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)

        # Ações
        actions = ttk.Frame(main, padding=8)
        actions.pack(fill=X)
        ttk.Button(actions, text="Exportar CSV", bootstyle=INFO, command=self._exportar_csv).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="🔄 Atualizar", bootstyle=SECONDARY, command=self._carregar_historico).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="Voltar", bootstyle=SECONDARY, command=self._voltar).pack(side=RIGHT, padx=6)

    # ---------------- carregar operadores ----------------
    def _carregar_operadores(self):
        try:
            ops = listar_operadores()  # (id, display, username)
            values = [f"{display} (id:{uid})" for uid, display, username in ops]
            self.combo_func['values'] = values
            if values:
                self.combo_func.current(0)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar operadores: {e}")

    # ---------------- decidir tipo automaticamente e registrar ----------------
    def _registrar_ponto(self):
        sel = self.combo_func.get()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um funcionário.")
            return
        try:
            uid = int(sel.split("id:")[-1].replace(")",""))
        except Exception:
            messagebox.showerror("Erro", "Não foi possível identificar o funcionário selecionado.")
            return

        # conta quantas batidas hoje (localtime) para decidir entrada/saida
        try:
            cont = contar_batidas_dia(uid)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao consultar batidas do dia: {e}")
            return

        # regra: se cont (quantidade já registradas hoje) for par -> próxima é ENTRADA
        # ex: cont=0 -> entrada, cont=1 -> saida, cont=2 -> entrada, etc
        tipo = "entrada" if (cont % 2 == 0) else "saida"

        try:
            bid = registrar_batida(uid, tipo)
            messagebox.showinfo("Registrado", f"Batida registrada (ID {bid}) — {tipo.capitalize()} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self._carregar_historico()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao registrar batida: {e}")

    # ---------------- carregar histórico ----------------
    def _carregar_historico(self):
        periodo = self.periodo_var.get()
        # se o combo estiver com um funcionario selecionado, filtrar por ele
        funcionario_id = None
        sel = self.combo_func.get()
        if sel:
            try:
                funcionario_id = int(sel.split("id:")[-1].replace(")",""))
            except Exception:
                funcionario_id = None
        try:
            rows = listar_batidas_periodo(periodo, funcionario_id)
            # limpa tree
            for r in self.tree.get_children():
                self.tree.delete(r)
            # cada row: (id, funcionario_id, tipo, timestamp, nome)
            for r in rows:
                bid, fid, tipo, ts, nome = r
                # mostra Batida como "Entrada" ou "Saída"
                display_tipo = "Entrada" if tipo.lower() == "entrada" else "Saída"
                self.tree.insert("", "end", values=(bid, nome, display_tipo, ts))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar histórico: {e}")

    # ---------------- exportar CSV ----------------
    def _exportar_csv(self):
        file = asksaveasfilename(defaultextension=".csv",
                                 filetypes=[("CSV","*.csv")],
                                 initialfile=f"ponto_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        if not file:
            return
        try:
            # filtra por funcionario se selecionado
            funcionario_id = None
            sel = self.combo_func.get()
            if sel:
                try:
                    funcionario_id = int(sel.split("id:")[-1].replace(")",""))
                except Exception:
                    funcionario_id = None
            exportar_csv(file, funcionario_id=funcionario_id)
            messagebox.showinfo("Sucesso", f"Arquivo salvo: {file}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar CSV: {e}")

    # ---------------- ajustar ponto (admin) - função simples de edição manual ----------------
    def _ajustar_ponto(self):
        # Aqui deixo uma interface simples: abre diálogo que informa que o ajuste deve ser feito por DB/admin
        messagebox.showinfo("Ajuste de Ponto", "Função de ajuste reduzida: para ajustar manualmente, edite o registro na tabela 'ponto_batidas' ou peça suporte ao administrador.")
        # Você pode expandir isso para abrir um diálogo que permita adicionar/remover batidas explicitamente (se quiser eu implemento).

    # ---------------- voltar ----------------
    def _voltar(self):
        if self.master:
            try:
                self.master.deiconify()
            except Exception:
                pass
            self.destroy()
        else:
            # fallback: abrir dashboard em novo processo (compat)
            try:
                from ui.dashboard_ui import DashboardUI
                self.destroy()
                DashboardUI().mainloop()
            except Exception:
                self.destroy()

