# ui/bater_ponto_ui.py — PARTE A
"""
UI: Bater Ponto (nova)
- botão único Registrar Ponto (grava 'entrada' ou 'saida' alternando)
- botão Ajustar Ponto (visível apenas para admin) — permite editar uma linha selecionada
- filtros: diário / semanal / mensal
- export CSV
- usa database/bater_ponto_db.py
"""
import os
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar
from tkinter.filedialog import asksaveasfilename
from datetime import datetime
# garante imports relativos
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from database.bater_ponto_db import (
    ensure_tables,
    listar_operadores,
    registrar_batida,
    listar_batidas_periodo,
    exportar_csv
)
# ui/bater_ponto_ui.py — PARTE B
class BaterPontoUI(ttk.Window):
    def __init__(self, master=None, operador_display=None, role="operador"):
        super().__init__(themename="superhero")
        self.master = master
        self.operador_display = operador_display
        self.role = role
        self.title("⏰ Registro de Ponto")
        self.geometry("900x600")
        self.minsize(900, 600)
        # garante tabela no DB
        ensure_tables()
        # vars
        self.funcionario_var = StringVar()
        self.filtro_periodo_var = StringVar(value="diario")
        self._build_ui()
        self._carregar_operadores()
        self._carregar_historico()
    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill=X)
        ttk.Label(header, text="Registro de Ponto", font=("Segoe UI", 18, "bold")).pack(side=LEFT)
        ttk.Label(header, text=f"Operador: {self.operador_display or '—'}", font=("Segoe UI", 10)).pack(side=RIGHT)
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)
        sel = ttk.Labelframe(main, text="Funcionário", padding=10)
        sel.pack(fill=X, pady=8)
        ttk.Label(sel, text="Funcionário:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.combo_func = ttk.Combobox(sel, textvariable=self.funcionario_var, state="readonly", width=40)
        self.combo_func.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        # Botões principais: registrar (único) e ajustar (admin)
        ttk.Button(sel, text="Registrar Ponto", bootstyle=SUCCESS, command=self._registrar_ponto).grid(row=0, column=2, padx=6)
        self.btn_ajustar = ttk.Button(sel, text="Ajustar Ponto", bootstyle=INFO, command=self._ajustar_ponto)
        self.btn_ajustar.grid(row=0, column=3, padx=6)
        if self.role != "admin":
            self.btn_ajustar.state(["disabled"])
        # filtro periodo
        filtro = ttk.Labelframe(main, text="Período", padding=10)
        filtro.pack(fill=X, pady=8)
        ttk.Radiobutton(filtro, text="Diário", value="diario", variable=self.filtro_periodo_var, command=self._carregar_historico).pack(side=LEFT, padx=10)
        ttk.Radiobutton(filtro, text="Semanal", value="semanal", variable=self.filtro_periodo_var, command=self._carregar_historico).pack(side=LEFT, padx=10)
        ttk.Radiobutton(filtro, text="Mensal", value="mensal", variable=self.filtro_periodo_var, command=self._carregar_historico).pack(side=LEFT, padx=10)
        # tabela
        hist = ttk.Labelframe(main, text="Histórico de Batidas", padding=10)
        hist.pack(fill="both", expand=True)
        cols = ("id", "func", "tipo", "timestamp")
        self.tree = ttk.Treeview(hist, columns=cols, show="headings")
        self.tree.heading("id", text="ID");     self.tree.column("id", width=60, anchor="center")
        self.tree.heading("func", text="Funcionário"); self.tree.column("func", width=220, anchor="center")
        self.tree.heading("tipo", text="Batida"); self.tree.column("tipo", width=140, anchor="center")
        self.tree.heading("timestamp", text="Data/Hora"); self.tree.column("timestamp", width=200, anchor="center")
        self.tree.pack(fill="both", expand=True, side=LEFT)
        vsb = ttk.Scrollbar(hist, command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        actions = ttk.Frame(main, padding=10)
        actions.pack(fill=X)
        ttk.Button(actions, text="Exportar CSV", bootstyle=INFO, command=self._exportar_csv).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="Atualizar", command=self._carregar_historico).pack(side=LEFT, padx=6)
        ttk.Button(actions, text="Voltar", bootstyle=SECONDARY, command=self._voltar).pack(side=RIGHT, padx=6)
# ui/bater_ponto_ui.py — PARTE C
    def _carregar_operadores(self):
        """Carrega apenas o NOME (sem id) no combo."""
        try:
            ops = listar_operadores()  # retorna (id, display_name, username)
            self._oper_map = {}  # map nome -> id (nome é único ou primeira ocorrência)
            values = []
            for uid, display, username in ops:
                name = display or username or f"user_{uid}"
                # evita colar (id:...) — apenas mostra nome
                values.append(name)
                # caso haja duplicidade de nomes, último sobrescreve — se for problema podemos usar chave composta
                self._oper_map[name] = uid
            self.combo_func['values'] = values
            if values:
                self.combo_func.current(0)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar operadores: {e}")
    def _registrar_ponto(self):
        sel = self.combo_func.get()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecione um funcionário.")
        uid = self._oper_map.get(sel)
        if not uid:
            return messagebox.showerror("Erro", "Funcionário não identificado.")
        # regra simples: alterna entrada/saida com base na quantidade de batidas do dia (impar -> entrada, par -> saida)
        try:
            # lista últimas batidas do funcionário (diário) para decidir próxima
            rows = listar_batidas_periodo("diario", funcionario_id=uid)
            # contar batidas do dia para ele; próxima batida: se count %2 == 0 -> entrada, else saida
            count = sum(1 for r in rows)
            tipo = "entrada" if (count % 2 == 0) else "saida"
            bid = registrar_batida(uid, tipo)
            messagebox.showinfo("Registrado", f"Batida registrada (ID {bid}) — {tipo.capitalize()}")
            self._carregar_historico()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao registrar batida: {e}")
    def _carregar_historico(self):
        periodo = self.filtro_periodo_var.get() or "diario"
        sel = self.combo_func.get()
        funcionario_id = None
        if sel:
            funcionario_id = self._oper_map.get(sel)
        try:
            rows = listar_batidas_periodo(periodo, funcionario_id=funcionario_id)
            # limpa e re-popula a tabela com formatação da data
            for r in self.tree.get_children():
                self.tree.delete(r)
            for row in rows:
                # row expected: (id, funcionario_id, tipo, timestamp, nome)
                bid, fid, tipo, ts, nome = row
                # formata ts: "AbrevDia MM-DD HH:MM" -> exemplo "Ter 11-25 21:47"
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    abrev = dt.strftime("%a")  # Mon -> Mon language locale, but short
                    ts_fmt = f"{abrev} {dt.strftime('%m-%d %H:%M')}"
                except Exception:
                    ts_fmt = ts
                # insere com colunas centralizadas via anchor já definido nas col configs
                self.tree.insert("", "end", values=(bid, nome, tipo.capitalize(), ts_fmt))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar histórico: {e}")
    def _exportar_csv(self):
        path = asksaveasfilename(defaultextension=".csv",
                                 initialfile=f"ponto_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                 filetypes=[("CSV", "*.csv")])
        if not path:
            return
        sel = self.combo_func.get()
        funcionario_id = self._oper_map.get(sel) if sel else None
        try:
            exportar_csv(path, funcionario_id=funcionario_id)
            messagebox.showinfo("Sucesso", f"Arquivo salvo: {path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar: {e}")
    def _ajustar_ponto(self):
        """Permite ajustar a linha selecionada (apenas admins têm esse botão ativo)."""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Selecione uma batida na lista para ajustar.")
        iid = sel[0]
        vals = self.tree.item(iid, "values")
        bid = vals[0]
        # abrir uma janela simples de edição com novo tipo e confirmar
        edit_win = ttk.Toplevel(self)
        edit_win.title(f"Ajustar Batida {bid}")
        edit_win.geometry("360x140")
        ttk.Label(edit_win, text=f"ID: {bid}").pack(pady=6)
        tipo_var = StringVar(value=vals[2])
        ttk.Label(edit_win, text="Tipo (Entrada/Saida):").pack()
        tipo_entry = ttk.Entry(edit_win, textvariable=tipo_var)
        tipo_entry.pack(pady=6)
        def _confirm():
            new_tipo = tipo_var.get().strip().lower()
            if new_tipo not in ("entrada", "saida"):
                return messagebox.showwarning("Aviso", "Tipo deve ser 'entrada' ou 'saida'.")
            # chama DB para atualizar (function update_batida precisa existir)
            try:
                from database.bater_ponto_db import atualizar_batida
                atualizar_batida(int(bid), new_tipo)
                messagebox.showinfo("OK", "Batida ajustada.")
                edit_win.destroy()
                self._carregar_historico()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao ajustar: {e}")
        ttk.Button(edit_win, text="OK", command=_confirm).pack(pady=6)
    def _voltar(self):
        if self.master:
            try:
                self.master.deiconify()
            except Exception:
                pass
            self.destroy()
        else:
            self.destroy()

