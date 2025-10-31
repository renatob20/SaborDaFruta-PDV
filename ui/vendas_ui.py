# ui/vendas_ui.py
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_PATH = os.path.join("database", "acaiteria.db")

def get_connection():
    """Retorna conexão com o DB unificado."""
    if not os.path.exists("database"):
        os.makedirs("database")
    return sqlite3.connect(DB_PATH)


class VendasUI(tk.Toplevel):
    """
    Tela de Vendas (janela filha).
    Uso: VendasUI(master=root, operador='Joao', role='operador')
    ou VendasUI(master=root, operador='admin', role='admin')
    """
    def __init__(self, master=None, operador="Operador", role="operador"):
        super().__init__(master)
        self.operador = operador
        self.role = role

        self.title(f"Vendas - {self.operador} ({self.role})")
        self.geometry("900x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self.carregar_vendas()  # carrega ao abrir

    def _build_ui(self):
        frame_top = tk.Frame(self)
        frame_top.pack(fill="x", padx=8, pady=6)

        # Formulário rápido
        tk.Label(frame_top, text="Tipo:").grid(row=0, column=0, sticky="w")
        self.tipo_cb = ttk.Combobox(frame_top, values=["Picolé", "Sorvete a Granel", "Copo 300ml", "Outros"], state="readonly")
        self.tipo_cb.current(0)
        self.tipo_cb.grid(row=0, column=1, padx=6)

        tk.Label(frame_top, text="Sabor:").grid(row=0, column=2, sticky="w")
        self.sabor_ent = tk.Entry(frame_top)
        self.sabor_ent.grid(row=0, column=3, padx=6)

        tk.Label(frame_top, text="Qtd (Kg/Unid):").grid(row=0, column=4, sticky="w")
        self.qtd_ent = tk.Entry(frame_top, width=8)
        self.qtd_ent.grid(row=0, column=5, padx=6)

        tk.Label(frame_top, text="Valor Unit (R$):").grid(row=0, column=6, sticky="w")
        self.valor_ent = tk.Entry(frame_top, width=10)
        self.valor_ent.grid(row=0, column=7, padx=6)

        tk.Label(frame_top, text="Pagamento:").grid(row=1, column=0, sticky="w", pady=6)
        self.pgto_cb = ttk.Combobox(frame_top, values=["Pix", "Crédito", "Débito", "Dinheiro"], state="readonly")
        self.pgto_cb.current(0)
        self.pgto_cb.grid(row=1, column=1, padx=6)

        tk.Label(frame_top, text="Observações:").grid(row=1, column=2, sticky="w")
        self.obs_ent = tk.Entry(frame_top, width=40)
        self.obs_ent.grid(row=1, column=3, columnspan=3, padx=6, sticky="w")

        btn_registrar = tk.Button(frame_top, text="Registrar Venda", command=self.on_registrar)
        btn_registrar.grid(row=1, column=7, padx=6)

        # Botões inferiores
        frame_mid = tk.Frame(self)
        frame_mid.pack(fill="x", padx=8, pady=6)
        self.btn_excluir = tk.Button(frame_mid, text="Excluir Venda Selecionada", command=self.on_excluir)
        self.btn_excluir.pack(side="left")
        if self.role != "admin":
            # operadores não podem excluir
            self.btn_excluir.config(state="disabled")

        self.btn_atualizar = tk.Button(frame_mid, text="Atualizar", command=self.carregar_vendas)
        self.btn_atualizar.pack(side="left", padx=6)

        # Tabela de vendas
        frame_table = tk.Frame(self)
        frame_table.pack(fill="both", expand=True, padx=8, pady=6)

        cols = ("id", "data_venda", "tipo_produto", "sabor", "quantidade", "valor_unit", "valor_total", "forma_pagamento", "operador")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            # coluna id menor
            width = 60 if c == "id" else 120
            self.tree.column(c, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Permitindo scroll vertical
        vsb = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

    def on_registrar(self):
        try:
            tipo = self.tipo_cb.get()
            sabor = self.sabor_ent.get().strip()
            qtd = float(self.qtd_ent.get())
            valor_unit = float(self.valor_ent.get())
            pgto = self.pgto_cb.get()
            obs = self.obs_ent.get().strip()

            conn = get_connection()
            cursor = conn.cursor()
            valor_total = qtd * valor_unit
            data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO vendas (data_venda, tipo_produto, sabor, quantidade, valor_unit, valor_total, forma_pagamento, operador, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data_venda, tipo, sabor, qtd, valor_unit, valor_total, pgto, self.operador, obs))
            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", f"Venda registrada (R$ {valor_total:.2f})")
            # limpa campos
            self.sabor_ent.delete(0, tk.END)
            self.qtd_ent.delete(0, tk.END)
            self.valor_ent.delete(0, tk.END)
            self.obs_ent.delete(0, tk.END)
            self.carregar_vendas()
        except ValueError:
            messagebox.showwarning("Entrada inválida", "Verifique quantidade e valor unitário (use ponto como decimal).")
        except sqlite3.Error as e:
            messagebox.showerror("Erro BD", f"Falha ao gravar venda: {e}")

    def carregar_vendas(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, data_venda, tipo_produto, sabor, quantidade, valor_unit, valor_total, forma_pagamento, operador
                FROM vendas
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
            conn.close()

            # atualiza tree
            for r in self.tree.get_children():
                self.tree.delete(r)
            for row in rows:
                self.tree.insert("", "end", values=row)
        except sqlite3.OperationalError as e:
            # tabela possivelmente não existe
            messagebox.showerror("Erro BD", f"Tabela 'vendas' não encontrada. Inicialize o banco: {e}")
        except sqlite3.Error as e:
            messagebox.showerror("Erro BD", f"Falha ao carregar vendas: {e}")

    def on_excluir(self):
        if self.role != "admin":
            messagebox.showwarning("Acesso negado", "Somente administradores podem excluir vendas.")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione uma venda para excluir.")
            return
        item = self.tree.item(sel[0])
        venda_id = item["values"][0]
        if messagebox.askyesno("Confirmar", f"Excluir venda ID {venda_id}?"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Removido", "Venda excluída.")
                self.carregar_vendas()
            except sqlite3.Error as e:
                messagebox.showerror("Erro BD", f"Falha ao excluir venda: {e}")

    def on_close(self):
        """Quando fechar janela, apenas destrói (retorna ao dashboard)"""
        self.destroy()
