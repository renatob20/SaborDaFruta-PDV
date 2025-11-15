# ui/vendas_ui.py
import os
import sys
from datetime import datetime
import sqlite3

# garante que imports relativos funcionem mesmo quando o módulo for executado diretamente
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, DoubleVar, IntVar

# importa função de conexão (se tiver outro nome ajuste para seu arquivo db)
try:
    from database.db import get_connection
except Exception:
    # fallback: conexão direta com o arquivo padrão
    def get_connection():
        db_path = os.path.join("database", "acaiteria.db")
        if not os.path.exists("database"):
            os.makedirs("database")
        return sqlite3.connect(db_path)


# ---------------------------------------------------------------------
# Funções de DB: criam tabelas necessárias (seguindo padrão do projeto)
# ---------------------------------------------------------------------
def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()

    # tabela vendas (cabeçalho da venda)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_venda TEXT NOT NULL,
        operador TEXT,
        total REAL NOT NULL,
        forma_pagamento TEXT,
        valor_recebido REAL,
        troco REAL
    )
    """)

    # tabela venda_items (itens da venda)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS venda_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER NOT NULL,
        produto_id INTEGER,
        produto_nome TEXT,
        tipo TEXT,
        quantidade INTEGER,
        peso_kg REAL,
        valor_unit REAL,
        subtotal REAL,
        FOREIGN KEY(venda_id) REFERENCES vendas(id)
    )
    """)

    # OBS: tabela produtos deve existir (models/produto_model.py já cria). Verifica não lança erro.
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# UI: Tela de Vendas (janela Toplevel)
# ---------------------------------------------------------------------
class VendasUI(ttk.Window):
    def __init__(self, master=None, operador="Operador", role="operador"):
        # usamos tema para ficar padronizado com produtos_ui
        super().__init__(themename="superhero")
        self.master = master
        self.operador = operador
        self.role = role

        self.title(f"Vendas - Operador: {self.operador}")
        self.geometry("1000x640")
        self.minsize(900, 560)

        # estado da venda atual (carrinho)
        self.carrinho = []  # lista de dicts {produto_id, produto_nome, tipo, quantidade, peso_kg, valor_unit, subtotal}
        self.produtos = []  # lista de produtos carregados do DB: (id, tipo, sabor/nome, preco, estoque)

        # garantir tabelas
        ensure_tables()

        # build UI e carregar produtos
        self._build_ui()
        self._carregar_produtos()
        self._carregar_vendas_recente()  # opcional: mostra últimas vendas

    # ---------------- UI ----------------
    def _build_ui(self):
        # Header
        hdr = ttk.Frame(self, padding=10)
        hdr.pack(fill=X)
        ttk.Label(hdr, text="Registrar Venda", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        ttk.Label(hdr, text=f"Operador: {self.operador}", font=("Segoe UI", 10)).pack(side=RIGHT)

        content = ttk.Frame(self, padding=10)
        content.pack(fill=BOTH, expand=True)

        # Left: Formulário seleção produto + carrinho
        left = ttk.Frame(content)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        # produto
        frm_prod = ttk.Labelframe(left, text="Adicionar item", padding=10)
        frm_prod.pack(fill=X, pady=4)

        ttk.Label(frm_prod, text="Produto:").grid(row=0, column=0, sticky=W, padx=6, pady=6)
        self.produto_cb = ttk.Combobox(frm_prod, state="readonly", width=40)
        self.produto_cb.grid(row=0, column=1, sticky=W, padx=6)
        self.produto_cb.bind("<<ComboboxSelected>>", lambda e: self._produto_selecionado())

        ttk.Label(frm_prod, text="Tipo/Unidade:").grid(row=1, column=0, sticky=W, padx=6, pady=6)
        self.tipo_label = ttk.Label(frm_prod, text="-")
        self.tipo_label.grid(row=1, column=1, sticky=W, padx=6)

        ttk.Label(frm_prod, text="Qtd (unid):").grid(row=2, column=0, sticky=W, padx=6, pady=6)
        self.qtd_var = StringVar()
        self.qtd_ent = ttk.Entry(frm_prod, textvariable=self.qtd_var, width=12)
        self.qtd_ent.grid(row=2, column=1, sticky=W, padx=6)

        ttk.Label(frm_prod, text="Peso (kg):").grid(row=3, column=0, sticky=W, padx=6, pady=6)
        self.peso_var = StringVar()
        self.peso_ent = ttk.Entry(frm_prod, textvariable=self.peso_var, width=12, state="disabled")
        self.peso_ent.grid(row=3, column=1, sticky=W, padx=6)

        ttk.Label(frm_prod, text="Valor Unitário (R$):").grid(row=4, column=0, sticky=W, padx=6, pady=6)
        self.valor_unit_var = StringVar()
        self.valor_unit_ent = ttk.Entry(frm_prod, textvariable=self.valor_unit_var, width=14, state="readonly")
        self.valor_unit_ent.grid(row=4, column=1, sticky=W, padx=6)

        ttk.Button(frm_prod, text="➕ Adicionar ao carrinho", bootstyle=SUCCESS, command=self.adicionar_carrinho).grid(row=5, column=0, columnspan=2, pady=10)

        # carrinho: Treeview
        cart_frame = ttk.Labelframe(left, text="Carrinho", padding=8)
        cart_frame.pack(fill=BOTH, expand=True, pady=6)

        cols = ("id", "produto", "tipo", "qtd", "peso_kg", "valor_unit", "subtotal")
        self.tree_cart = ttk.Treeview(cart_frame, columns=cols, show="headings")
        headings = {
            "id": "ID",
            "produto": "Produto",
            "tipo": "Tipo",
            "qtd": "Qtd",
            "peso_kg": "Peso (kg)",
            "valor_unit": "R$/Unid",
            "subtotal": "Subtotal"
        }
        for c in cols:
            self.tree_cart.heading(c, text=headings[c])
            self.tree_cart.column(c, anchor=CENTER, width=90 if c in ("id","qtd") else 150)
        self.tree_cart.pack(fill=BOTH, expand=True, side=LEFT)

        sb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree_cart.yview)
        self.tree_cart.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)

        # ações do carrinho
        cart_actions = ttk.Frame(left)
        cart_actions.pack(fill=X, pady=6)
        ttk.Button(cart_actions, text="✏️ Editar item", command=self.editar_item).pack(side=LEFT, padx=6)
        ttk.Button(cart_actions, text="🗑️ Remover item", bootstyle=DANGER, command=self.remover_item).pack(side=LEFT, padx=6)
        ttk.Button(cart_actions, text="🔄 Limpar carrinho", bootstyle=SECONDARY, command=self.limpar_carrinho).pack(side=RIGHT, padx=6)

        # Right: Pagamento e resumo
        right = ttk.Frame(content, width=320)
        right.pack(side=RIGHT, fill=Y)

        resumo = ttk.Labelframe(right, text="Resumo da Venda", padding=12)
        resumo.pack(fill=X, pady=6)

        ttk.Label(resumo, text="Total (R$):").grid(row=0, column=0, sticky=W, pady=6)
        self.total_var = DoubleVar(value=0.0)
        self.total_ent = ttk.Entry(resumo, textvariable=self.total_var, state="readonly", width=20)
        self.total_ent.grid(row=0, column=1, padx=6)

        ttk.Label(resumo, text="Forma de Pagamento:").grid(row=1, column=0, sticky=W, pady=6)
        self.forma_cb = ttk.Combobox(resumo, values=["Pix", "Crédito", "Débito", "Dinheiro"], state="readonly", width=18)
        self.forma_cb.grid(row=1, column=1, padx=6)
        self.forma_cb.bind("<<ComboboxSelected>>", lambda e: self._on_forma_pagamento())

        ttk.Label(resumo, text="Valor Recebido (R$):").grid(row=2, column=0, sticky=W, pady=6)
        self.recebido_var = StringVar()
        self.recebido_ent = ttk.Entry(resumo, textvariable=self.recebido_var, state="disabled", width=20)
        self.recebido_ent.grid(row=2, column=1, padx=6)
        self.recebido_ent.bind("<KeyRelease>", lambda e: self._calcular_troco())

        ttk.Label(resumo, text="Troco (R$):").grid(row=3, column=0, sticky=W, pady=6)
        self.troco_var = DoubleVar(value=0.0)
        self.troco_ent = ttk.Entry(resumo, textvariable=self.troco_var, state="readonly", width=20)
        self.troco_ent.grid(row=3, column=1, padx=6)

        ttk.Button(resumo, text="✔️ Finalizar Venda", bootstyle=SUCCESS, command=self.finalizar_venda).grid(row=4, column=0, columnspan=2, pady=12)

        # Lista rápida de vendas recentes (opcional)
        recent = ttk.Labelframe(right, text="Últimas Vendas", padding=8)
        recent.pack(fill=BOTH, expand=True, pady=8)
        self.lst_recent = ttk.Treeview(recent, columns=("id","data","total","operador"), show="headings", height=6)
        self.lst_recent.heading("id", text="ID")
        self.lst_recent.heading("data", text="Data")
        self.lst_recent.heading("total", text="Total R$")
        self.lst_recent.heading("operador", text="Operador")
        self.lst_recent.column("id", width=50, anchor=CENTER)
        self.lst_recent.column("data", width=140)
        self.lst_recent.column("total", width=80, anchor=E)
        self.lst_recent.column("operador", width=100)
        self.lst_recent.pack(fill=BOTH, expand=True)

    # ---------------- carregamento produtos ----------------
    def _carregar_produtos(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, tipo, sabor, preco, estoque FROM produtos ORDER BY tipo, sabor")
            rows = cur.fetchall()
            conn.close()
            # produto: (id, tipo, sabor, preco, estoque)
            self.produtos = rows
            display = [f"{r[2]} — R$ {float(r[3]):.2f}" for r in rows]
            self.produto_cb['values'] = display
        except sqlite3.Error as e:
            messagebox.showerror("Erro ao carregar produtos", f"{e}")

    # ---------------- evento produto selecionado ----------------
    def _produto_selecionado(self):
        sel = self.produto_cb.get()
        if not sel:
            return
        # encontra produto pela descrição iniciada por sabor
        nome = sel.split(" — ")[0].strip()
        item = next((r for r in self.produtos if r[2] == nome), None)
        if item:
            _, tipo, sabor, preco, estoque = item
            self.tipo_label.config(text=tipo)
            self.valor_unit_var.set(f"{float(preco):.2f}")
            # se for por kg ativa campo peso
            if tipo.lower() == "kg" or "granel" in sabor.lower():
                self.peso_ent.config(state="normal")
                self.qtd_ent.config(state="disabled")
            else:
                self.peso_ent.config(state="disabled")
                self.qtd_ent.config(state="normal")

    # ---------------- adicionar ao carrinho ----------------
    def adicionar_carrinho(self):
        sel = self.produto_cb.get()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        nome = sel.split(" — ")[0].strip()
        prod = next((r for r in self.produtos if r[2] == nome), None)
        if not prod:
            messagebox.showerror("Erro", "Produto não encontrado.")
            return
        prod_id, tipo, sabor, preco, estoque = prod

        # ler quantidade ou peso conforme tipo
        if tipo.lower() == "kg" or "granel" in sabor.lower():
            try:
                peso = float(self.peso_var.get().replace(",", "."))
                quantidade = None
                if peso <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showwarning("Atenção", "Informe o peso válido em kg.")
                return
            subtotal = peso * float(preco)
        else:
            try:
                quantidade = int(self.qtd_var.get())
                peso = None
                if quantidade <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showwarning("Atenção", "Informe a quantidade (inteiro).")
                return
            subtotal = quantidade * float(preco)

        # adiciona ao carrinho e atualiza tree
        item = {
            "produto_id": prod_id,
            "produto_nome": sabor,
            "tipo": tipo,
            "quantidade": quantidade,
            "peso_kg": peso,
            "valor_unit": float(preco),
            "subtotal": float(subtotal)
        }
        self.carrinho.append(item)
        self._refresh_carrinho()
        self._recalcular_total()

        # limpa campos
        self.qtd_var.set("")
        self.peso_var.set("")

    def _refresh_carrinho(self):
        # limpa tree
        for r in self.tree_cart.get_children():
            self.tree_cart.delete(r)
        # popula
        for i, it in enumerate(self.carrinho, start=1):
            self.tree_cart.insert("", "end", iid=str(i-1), values=(
                it["produto_id"], it["produto_nome"], it["tipo"],
                it["quantidade"] if it["quantidade"] is not None else "",
                f"{it['peso_kg']:.3f}" if it["peso_kg"] is not None else "",
                f"{it['valor_unit']:.2f}", f"{it['subtotal']:.2f}"
            ))

    def _recalcular_total(self):
        total = sum(it["subtotal"] for it in self.carrinho)
        self.total_var.set(round(total, 2))
        # atualiza troco se já tiver valor recebido
        self._calcular_troco()

    def editar_item(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um item para editar.")
            return
        idx = int(sel[0])
        it = self.carrinho[idx]
        # preenche campos para edição
        # seleciona produto no combobox
        # buscamos por produto_nome
        prod_display = next((f"{r[2]} — R$ {float(r[3]):.2f}" for r in self.produtos if r[2] == it["produto_nome"]), None)
        if prod_display:
            self.produto_cb.set(prod_display)
            self._produto_selecionado()
            if it["tipo"].lower() == "kg" or it["peso_kg"]:
                self.peso_var.set(str(it["peso_kg"] or ""))
            else:
                self.qtd_var.set(str(it["quantidade"] or ""))
            # remove item antigo
            self.carrinho.pop(idx)
            self._refresh_carrinho()
            self._recalcular_total()
        else:
            messagebox.showerror("Erro", "Produto para edição não encontrado.")

    def remover_item(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um item para remover.")
            return
        idx = int(sel[0])
        self.carrinho.pop(idx)
        self._refresh_carrinho()
        self._recalcular_total()

    def limpar_carrinho(self):
        if not self.carrinho:
            return
        if messagebox.askyesno("Confirmar", "Deseja limpar todo o carrinho?"):
            self.carrinho.clear()
            self._refresh_carrinho()
            self._recalcular_total()

    # ---------------- pagamento ----------------
    def _on_forma_pagamento(self):
        forma = self.forma_cb.get()
        if forma == "Dinheiro":
            self.recebido_ent.config(state="normal")
        else:
            self.recebido_var.set("")
            self.recebido_ent.config(state="disabled")
            self.troco_var.set(0.0)

    def _calcular_troco(self):
        try:
            total = float(self.total_var.get())
            recebido = float(self.recebido_var.get().replace(",", ".")) if self.recebido_var.get() else 0.0
            troco = max(0.0, recebido - total)
            self.troco_var.set(round(troco, 2))
        except Exception:
            self.troco_var.set(0.0)

    # ---------------- finalizar venda ----------------
    def finalizar_venda(self):
        if not self.carrinho:
            messagebox.showwarning("Atenção", "Carrinho vazio.")
            return
        forma = self.forma_cb.get()
        if not forma:
            messagebox.showwarning("Atenção", "Selecione a forma de pagamento.")
            return

        total = float(self.total_var.get())
        recebido = float(self.recebido_var.get().replace(",", ".")) if self.recebido_var.get() else None
        troco = float(self.troco_var.get()) if self.troco_var.get() else 0.0

        if forma == "Dinheiro" and (recebido is None or recebido < total):
            messagebox.showwarning("Atenção", "Valor recebido insuficiente.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            # inserir cabeçalho venda
            cur.execute("""
                INSERT INTO vendas (data_venda, operador, total, forma_pagamento, valor_recebido, troco)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.operador, total, forma, recebido, troco))
            venda_id = cur.lastrowid

            # inserir itens
            for it in self.carrinho:
                cur.execute("""
                    INSERT INTO venda_items (venda_id, produto_id, produto_nome, tipo, quantidade, peso_kg, valor_unit, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    venda_id,
                    it.get("produto_id"),
                    it.get("produto_nome"),
                    it.get("tipo"),
                    it.get("quantidade"),
                    it.get("peso_kg"),
                    it.get("valor_unit"),
                    it.get("subtotal")
                ))
                # opcional: atualiza estoque quando for por unidade
                if it.get("quantidade") is not None:
                    try:
                        # decrementa estoque se campo existir
                        conn2 = get_connection()
                        c2 = conn2.cursor()
                        c2.execute("SELECT estoque FROM produtos WHERE id = ?", (it["produto_id"],))
                        row = c2.fetchone()
                        if row:
                            novo = max(0, int(row[0]) - int(it["quantidade"]))
                            c2.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (novo, it["produto_id"]))
                            conn2.commit()
                        conn2.close()
                    except Exception:
                        pass

            conn.commit()
            conn.close()

            messagebox.showinfo("Venda registrada", f"Venda ID {venda_id} registrada com sucesso!\nTotal: R$ {total:.2f}")
            # limpa tudo
            self.carrinho.clear()
            self._refresh_carrinho()
            self._recalcular_total()
            self.forma_cb.set("")
            self.recebido_var.set("")
            self.troco_var.set(0.0)
            self._carregar_vendas_recente()

        except sqlite3.Error as e:
            messagebox.showerror("Erro BD", f"Falha ao gravar venda: {e}")

    # ---------------- carregar vendas recentes ----------------
    def _carregar_vendas_recente(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, data_venda, total, operador FROM vendas ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
            conn.close()
            for r in self.lst_recent.get_children():
                self.lst_recent.delete(r)
            for r in rows:
                self.lst_recent.insert("", "end", values=(r[0], r[1], f"{float(r[2]):.2f}", r[3]))
        except Exception:
            pass


# Execução direta para testes
if __name__ == "__main__":
    app = VendasUI(operador="Teste", role="operador")
    app.mainloop()
