import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


DB_PATH = os.path.join("database", "acaiteria.db")


def get_connection():
    """Retorna conexão com o banco."""
    if not os.path.exists("database"):
        os.makedirs("database")
    return sqlite3.connect(DB_PATH)


class VendasUI(tk.Toplevel):
    """
    Tela de vendas com:
    - Lista de produtos cadastrados
    - Cálculo automático do valor total
    - Cálculo de troco ao pagar em Dinheiro
    - Registro da venda no banco
    """

    def __init__(self, master=None, operador="Operador", role="operador"):
        super().__init__(master)
        self.operador = operador
        self.role = role

        self.title(f"Vendas - Operador: {self.operador}")
        self.geometry("950x600")
        self.configure(background="#f8f8f8")
        self.resizable(False, False)

        self.preco_selecionado = 0.0

        self.build_ui()
        self.load_produtos()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        # ---------------- CABEÇALHO ----------------
        ttk.Label(frame, text="Registrar Venda", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=4, pady=10)

        # ---------------- PRODUTO ----------------
        ttk.Label(frame, text="Produto:", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w")
        self.produto_cb = ttk.Combobox(frame, state="readonly", width=35)
        self.produto_cb.grid(row=1, column=1, padx=10, pady=5)
        self.produto_cb.bind("<<ComboboxSelected>>", self.on_produto_selecionado)

        # ---------------- QUANTIDADE ----------------
        ttk.Label(frame, text="Quantidade:", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="w")
        self.qtd_entry = ttk.Entry(frame, width=10)
        self.qtd_entry.grid(row=2, column=1, sticky="w", pady=5)
        self.qtd_entry.bind("<KeyRelease>", lambda e: self.atualizar_total())

        # ---------------- PREÇO UNITÁRIO ----------------
        ttk.Label(frame, text="Preço Unitário (R$):", font=("Segoe UI", 11)).grid(row=3, column=0, sticky="w")
        self.preco_entry = ttk.Entry(frame, width=15, state="readonly")
        self.preco_entry.grid(row=3, column=1, sticky="w", pady=5)

        # ---------------- FORMA DE PAGAMENTO ----------------
        ttk.Label(frame, text="Pagamento:", font=("Segoe UI", 11)).grid(row=4, column=0, sticky="w")
        self.pagamento_cb = ttk.Combobox(frame, values=["Pix", "Crédito", "Débito", "Dinheiro"], state="readonly", width=15)
        self.pagamento_cb.grid(row=4, column=1, sticky="w", pady=5)
        self.pagamento_cb.bind("<<ComboboxSelected>>", self.on_pagamento_alterado)

        # ---------------- VALOR TOTAL ----------------
        ttk.Label(frame, text="Valor Total (R$):", font=("Segoe UI", 11)).grid(row=5, column=0, sticky="w")
        self.total_entry = ttk.Entry(frame, width=20, state="readonly")
        self.total_entry.grid(row=5, column=1, sticky="w", pady=5)

        # ---------------- VALOR RECEBIDO (somente DINHEIRO) ----------------
        ttk.Label(frame, text="Valor Recebido (R$):", font=("Segoe UI", 11)).grid(row=6, column=0, sticky="w")
        self.recebido_entry = ttk.Entry(frame, width=15, state="disabled")
        self.recebido_entry.grid(row=6, column=1, sticky="w", pady=5)
        self.recebido_entry.bind("<KeyRelease>", lambda e: self.calcular_troco())

        # ---------------- TROCO ----------------
        ttk.Label(frame, text="Troco (R$):", font=("Segoe UI", 11)).grid(row=7, column=0, sticky="w")
        self.troco_entry = ttk.Entry(frame, width=15, state="readonly")
        self.troco_entry.grid(row=7, column=1, sticky="w", pady=5)

        # ---------------- BOTÃO REGISTRAR ----------------
        self.btn_registrar = ttk.Button(frame, text="Registrar Venda", command=self.registrar_venda)
        self.btn_registrar.grid(row=8, column=0, columnspan=2, pady=20)

    # ---------------------------------------------------------
    # FUNÇÕES
    # ---------------------------------------------------------
    def load_produtos(self):
        """Carrega lista de produtos do banco."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nome, preco FROM produtos ORDER BY nome")
            produtos = cursor.fetchall()
            conn.close()

            self.lista_produtos = produtos
            self.produto_cb["values"] = [p[0] for p in produtos]

        except sqlite3.Error as e:
            messagebox.showerror("Erro ao carregar produtos", str(e))

    def on_produto_selecionado(self, event=None):
        """Atualiza preço conforme produto escolhido."""
        nome = self.produto_cb.get()
        for produto, preco in self.lista_produtos:
            if produto == nome:
                self.preco_selecionado = preco
                self.preco_entry.configure(state="normal")
                self.preco_entry.delete(0, tk.END)
                self.preco_entry.insert(0, f"{preco:.2f}")
                self.preco_entry.configure(state="readonly")
                break
        self.atualizar_total()

    def atualizar_total(self):
        try:
            qtd = float(self.qtd_entry.get())
            total = qtd * self.preco_selecionado
            self.total_entry.configure(state="normal")
            self.total_entry.delete(0, tk.END)
            self.total_entry.insert(0, f"{total:.2f}")
            self.total_entry.configure(state="readonly")
        except:
            self.total_entry.configure(state="normal")
            self.total_entry.delete(0, tk.END)
            self.total_entry.insert(0, "0.00")
            self.total_entry.configure(state="readonly")

    def on_pagamento_alterado(self, event=None):
        """Ativa campo 'valor recebido' apenas no pagamento em dinheiro."""
        if self.pagamento_cb.get() == "Dinheiro":
            self.recebido_entry.configure(state="normal")
        else:
            self.recebido_entry.configure(state="disabled")
            self.recebido_entry.delete(0, tk.END)
            self.troco_entry.configure(state="normal")
            self.troco_entry.delete(0, tk.END)
            self.troco_entry.insert(0, "0.00")
            self.troco_entry.configure(state="readonly")

    def calcular_troco(self):
        try:
            valor_total = float(self.total_entry.get())
            recebido = float(self.recebido_entry.get())
            troco = recebido - valor_total
            self.troco_entry.configure(state="normal")
            self.troco_entry.delete(0, tk.END)
            self.troco_entry.insert(0, f"{troco:.2f}")
            self.troco_entry.configure(state="readonly")
        except:
            pass

    def registrar_venda(self):
        try:
            produto = self.produto_cb.get()
            qtd = float(self.qtd_entry.get())
            preco = float(self.preco_entry.get())
            total = float(self.total_entry.get())
            pagamento = self.pagamento_cb.get()
            recebido = self.recebido_entry.get()
            troco = self.troco_entry.get()

            if not produto:
                messagebox.showwarning("Atenção", "Selecione um produto.")
                return

            if pagamento == "Dinheiro" and (recebido == "" or float(recebido) < total):
                messagebox.showwarning("Atenção", "Valor recebido insuficiente.")
                return

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO vendas
                (data_venda, produto, quantidade, valor_unit, valor_total, pagamento, operador, valor_recebido, troco)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                produto,
                qtd,
                preco,
                total,
                pagamento,
                self.operador,
                float(recebido) if recebido else None,
                float(troco) if troco else 0
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", "Venda registrada!")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro ao registrar a venda", str(e))


# adiciona este bloco ao final do arquivo para testes independentes
if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # esconde a janela root, vamos usar apenas a Toplevel de vendas
    win = VendasUI(master=root, operador="Teste", role="operador")
    win.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
    root.mainloop()
