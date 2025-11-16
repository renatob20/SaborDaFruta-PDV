# ui/vendas_ui.py
import os
import sys
import sqlite3
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, DoubleVar, IntVar

# garante que imports relativos funcionem quando executado diretamente
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# try importar get_connection a partir do seu módulo database/db.py
try:
    from database.db import get_connection
except Exception:
    # fallback simples
    def get_connection():
        db_path = os.path.join("database", "acaiteria.db")
        if not os.path.exists("database"):
            os.makedirs("database")
        return sqlite3.connect(db_path)


# ----------------- Helpers -----------------
def brl_format(value):
    """Formata float -> '0,00' (BRL style)."""
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def to_float_from_brl(text):
    """Converte '1.234,56' ou '1234.56' ou '1234,56' -> float"""
    if text is None or text == "":
        return 0.0
    t = str(text).strip()
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except Exception:
        return 0.0


# ----------------- DB init (garante tabelas) -----------------
def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda TEXT NOT NULL,
            operador TEXT,
            total REAL NOT NULL,
            forma_pagamento TEXT,
            valor_recebido REAL,
            troco REAL
        );
    """)
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
        );
    """)
    conn.commit()
    conn.close()


# ----------------- UI: VendasUI -----------------
class VendasUI(ttk.Window):
    def __init__(self, master=None, operador="Operador", role="operador"):
        # usa tema padronizado
        super().__init__(themename="superhero")
        self.master = master
        self.operador = operador
        self.role = role

        # maximiza a janela ao abrir
        try:
            self.state("zoomed")
        except Exception:
            pass

        self.title(f"Vendas - Operador: {self.operador}")
        self.minsize(900, 560)

        # dados
        self.produtos = []          # tuplas: (id, tipo, sabor, preco, estoque)
        self.produtos_cache = {}    # label -> (id, tipo, sabor, preco)
        self.carrinho = []          # lista de dicts de itens
        self.total = 0.0

        # garantir tabelas
        ensure_tables()

        self._build_ui()
        self._carregar_tipos()      # popula tipos e depois sabores
        self._carregar_vendas_recentes()

    # ---------------- UI builder ----------------
    def _build_ui(self):
        # Header
        header = ttk.Frame(self, padding=10)
        header.pack(fill=X)
        ttk.Label(header, text="Registrar Venda", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        ttk.Label(header, text=f"Operador: {self.operador}", font=("Segoe UI", 10)).pack(side=RIGHT)

        main = ttk.Frame(self, padding=10)
        main.pack(fill=BOTH, expand=True)

        # left: seleção + carrinho
        left = ttk.Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        # -> Seletor tipo e sabor
        frm_sel = ttk.Labelframe(left, text="Adicionar item", padding=10)
        frm_sel.pack(fill=X, pady=4)

        ttk.Label(frm_sel, text="Tipo:").grid(row=0, column=0, sticky=W, padx=6, pady=6)
        self.tipo_cb = ttk.Combobox(frm_sel, state="readonly", width=30)
        self.tipo_cb.grid(row=0, column=1, sticky=W, padx=6)
        self.tipo_cb.bind("<<ComboboxSelected>>", lambda e: self._on_tipo_selected())

        ttk.Label(frm_sel, text="Sabor / Produto:").grid(row=1, column=0, sticky=W, padx=6, pady=6)
        self.sabor_cb = ttk.Combobox(frm_sel, state="readonly", width=50)
        self.sabor_cb.grid(row=1, column=1, sticky=W, padx=6)
        self.sabor_cb.bind("<<ComboboxSelected>>", lambda e: self._on_sabor_selected())

        # tipo / unidade label
        ttk.Label(frm_sel, text="Tipo/Unidade:").grid(row=2, column=0, sticky=W, padx=6, pady=6)
        self.tipo_label = ttk.Label(frm_sel, text="-")
        self.tipo_label.grid(row=2, column=1, sticky=W, padx=6)

        # qtd / peso
        ttk.Label(frm_sel, text="Qtd (unid):").grid(row=3, column=0, sticky=W, padx=6, pady=6)
        self.qtd_var = StringVar(value="")
        self.qtd_ent = ttk.Entry(frm_sel, textvariable=self.qtd_var, width=12)
        self.qtd_ent.grid(row=3, column=1, sticky=W, padx=6)

        ttk.Label(frm_sel, text="Peso (kg):").grid(row=4, column=0, sticky=W, padx=6, pady=6)
        self.peso_var = StringVar(value="")
        self.peso_ent = ttk.Entry(frm_sel, textvariable=self.peso_var, width=12, state="disabled")
        self.peso_ent.grid(row=4, column=1, sticky=W, padx=6)

        # valor unitário (oculto visualmente? deixamos readonly e pequeno)
        ttk.Label(frm_sel, text="Valor Unitário (R$):").grid(row=5, column=0, sticky=W, padx=6, pady=6)
        self.valor_unit_var = StringVar(value="0,00")
        self.valor_unit_ent = ttk.Entry(frm_sel, textvariable=self.valor_unit_var, width=14, state="readonly")
        self.valor_unit_ent.grid(row=5, column=1, sticky=W, padx=6)

        ttk.Button(frm_sel, text="➕ Adicionar ao carrinho", bootstyle=SUCCESS, command=self.adicionar_ao_carrinho).grid(row=6, column=0, columnspan=2, pady=10)

        # Carrinho Treeview
        cart_frame = ttk.Labelframe(left, text="Carrinho", padding=6)
        cart_frame.pack(fill=BOTH, expand=True, pady=6)

        cols = ("id", "produto", "tipo", "qtd", "peso_kg", "valor_unit", "subtotal")
        self.tree_cart = ttk.Treeview(cart_frame, columns=cols, show="headings", selectmode="browse")
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
            self.tree_cart.heading(c, text=headings[c], anchor="center")
            self.tree_cart.column(c, anchor="center", width=100 if c in ("id","qtd") else 160)
        self.tree_cart.pack(fill=BOTH, expand=True, side=LEFT)

        sb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree_cart.yview)
        self.tree_cart.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)

        # ações carrinho
        cart_actions = ttk.Frame(left)
        cart_actions.pack(fill=X, pady=6)
        ttk.Button(cart_actions, text="✏️ Editar item", command=self.editar_item).pack(side=LEFT, padx=6)
        ttk.Button(cart_actions, text="🗑️ Remover item", bootstyle=DANGER, command=self.remover_item).pack(side=LEFT, padx=6)
        ttk.Button(cart_actions, text="🔄 Limpar carrinho", bootstyle=SECONDARY, command=self.limpar_carrinho).pack(side=RIGHT, padx=6)

        # right: resumo + últimas vendas
        right = ttk.Frame(main, width=340)
        right.pack(side=RIGHT, fill=Y)

        resumo = ttk.Labelframe(right, text="Resumo da Venda", padding=10)
        resumo.pack(fill=X, pady=6)

        ttk.Label(resumo, text="Total (R$):").grid(row=0, column=0, sticky=W, pady=6)
        self.total_var = StringVar(value=brl_format(0.0))
        self.total_ent = ttk.Entry(resumo, textvariable=self.total_var, state="readonly", width=18)
        self.total_ent.grid(row=0, column=1, padx=6)

        ttk.Label(resumo, text="Forma de Pagamento:").grid(row=1, column=0, sticky=W, pady=6)
        self.forma_cb = ttk.Combobox(resumo, values=["Pix", "Crédito", "Débito", "Dinheiro"], state="readonly", width=16)
        self.forma_cb.grid(row=1, column=1, padx=6)
        self.forma_cb.bind("<<ComboboxSelected>>", lambda e: self._on_forma_change())

        ttk.Label(resumo, text="Valor Recebido (R$):").grid(row=2, column=0, sticky=W, pady=6)
        self.recebido_var = StringVar(value=brl_format(0.0))
        self.recebido_ent = ttk.Entry(resumo, textvariable=self.recebido_var, width=18, state="disabled")
        self.recebido_ent.grid(row=2, column=1, padx=6)
        self.recebido_ent.bind("<KeyRelease>", lambda e: self._atualizar_troco())

        ttk.Label(resumo, text="Troco (R$):").grid(row=3, column=0, sticky=W, pady=6)
        self.troco_var = StringVar(value=brl_format(0.0))
        self.troco_ent = ttk.Entry(resumo, textvariable=self.troco_var, state="readonly", width=18)
        self.troco_ent.grid(row=3, column=1, padx=6)

        ttk.Button(resumo, text="✔️ Finalizar Venda", bootstyle=SUCCESS, command=self.finalizar_venda).grid(row=4, column=0, columnspan=2, pady=12)

        # últimas vendas
        recent = ttk.Labelframe(right, text="Últimas Vendas", padding=8)
        recent.pack(fill=BOTH, expand=True, pady=6)
        self.tree_recent = ttk.Treeview(recent, columns=("id","data","total","operador"), show="headings", height=8)
        self.tree_recent.heading("id", text="ID", anchor="center")
        self.tree_recent.heading("data", text="Data", anchor="center")
        self.tree_recent.heading("total", text="Total R$", anchor="center")
        self.tree_recent.heading("operador", text="Operador", anchor="center")
        self.tree_recent.column("id", width=50, anchor="center")
        self.tree_recent.column("data", width=160, anchor="center")
        self.tree_recent.column("total", width=90, anchor="center")
        self.tree_recent.column("operador", width=100, anchor="center")
        self.tree_recent.pack(fill=BOTH, expand=True)

    # ---------------- carregar tipos (distinct) ----------------
    def _carregar_tipos(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT tipo FROM produtos ORDER BY tipo ASC")
            tipos = [r[0] for r in cur.fetchall()]
            conn.close()
            self.tipo_cb['values'] = tipos
            # também carrega cache completo de produtos para facilitar buscas
            self._carregar_todos_produtos_cache()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar tipos: {e}")

    def _carregar_todos_produtos_cache(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, tipo, sabor, preco, estoque FROM produtos")
            rows = cur.fetchall()
            conn.close()
            self.produtos = rows
        except Exception:
            self.produtos = []

    # ---------------- quando seleciona tipo -> carrega sabores correspondentes
    def _on_tipo_selected(self):
        tipo = self.tipo_cb.get()
        if not tipo:
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, sabor, preco FROM produtos WHERE tipo=? ORDER BY sabor", (tipo,))
            rows = cur.fetchall()
            conn.close()
            display = []
            self.produtos_cache.clear()
            for r in rows:
                pid, sabor, preco = r
                label = f"{sabor} — R$ {float(preco):.2f}"
                display.append(label)
                self.produtos_cache[label] = (pid, tipo, sabor, float(preco))
            self.sabor_cb['values'] = display
            # ativa campos conforme o tipo
            if tipo.lower() == "sorvete":
                self.peso_ent.config(state="normal")
                self.qtd_ent.config(state="disabled")
            else:
                self.peso_ent.config(state="disabled")
                self.qtd_ent.config(state="normal")
            # limpa seleção anterior
            self.sabor_cb.set("")
            self.valor_unit_var.set(brl_format(0.0))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar sabores: {e}")

    # ---------------- quando seleciona sabor -> atualiza preço
    def _on_sabor_selected(self):
        sel = self.sabor_cb.get()
        if sel and sel in self.produtos_cache:
            _, tipo, sabor, preco = self.produtos_cache[sel]
            self.tipo_label.config(text=tipo)
            self.valor_unit_var.set(brl_format(preco))
            # habilita campo correto
            if tipo.lower() == "sorvete":
                self.peso_ent.config(state="normal")
                self.qtd_ent.config(state="disabled")
            else:
                self.peso_ent.config(state="disabled")
                self.qtd_ent.config(state="normal")
        else:
            self.valor_unit_var.set(brl_format(0.0))

    # ---------------- adicionar item ----------------
    def adicionar_ao_carrinho(self):
        sel = self.sabor_cb.get()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione Tipo e Sabor/Produto.")
            return
        prod_info = self.produtos_cache.get(sel)
        if not prod_info:
            messagebox.showerror("Erro", "Produto não encontrado.")
            return
        pid, tipo, sabor, preco = prod_info

        if tipo.lower() == "sorvete":
            peso = to_float_from_brl(self.peso_var.get())
            if peso <= 0:
                messagebox.showwarning("Atenção", "Informe um peso válido (kg).")
                return
            quantidade = None
            subtotal = round(peso * preco, 2)
        else:
            try:
                quantidade = int(self.qtd_var.get())
            except Exception:
                quantidade = 0
            if quantidade <= 0:
                messagebox.showwarning("Atenção", "Informe uma quantidade válida.")
                return
            peso = None
            subtotal = round(quantidade * preco, 2)

        item = {
            "produto_id": pid,
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
        # preenche
        for idx, it in enumerate(self.carrinho):
            self.tree_cart.insert("", "end", iid=str(idx),
                                  values=(
                                      it["produto_id"],
                                      it["produto_nome"],
                                      it["tipo"],
                                      it["quantidade"] if it["quantidade"] is not None else "",
                                      f"{it['peso_kg']:.3f}" if it["peso_kg"] is not None else "",
                                      brl_format(it["valor_unit"]),
                                      brl_format(it["subtotal"])
                                  ))

    def _recalcular_total(self):
        total = sum(it["subtotal"] for it in self.carrinho)
        self.total = float(total)
        self.total_var.set(brl_format(self.total))
        self._atualizar_troco()

    # ---------------- editar / remover ----------------
    def editar_item(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um item para editar.")
            return
        idx = int(sel[0])
        item = self.carrinho.pop(idx)
        # pré-seleciona produto
        display = next((k for k, v in self.produtos_cache.items() if v[2] == item["produto_nome"]), None)
        if display:
            self.sabor_cb.set(display)
            self._on_sabor_selected()
            if item["tipo"].lower() == "sorvete":
                self.peso_var.set(str(item["peso_kg"] or ""))
            else:
                self.qtd_var.set(str(item["quantidade"] or ""))
        self._refresh_carrinho()
        self._recalcular_total()

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
        if messagebox.askyesno("Confirmar", "Deseja limpar o carrinho?"):
            self.carrinho.clear()
            self._refresh_carrinho()
            self._recalcular_total()

    # ---------------- pagamento / troco ----------------
    def _on_forma_change(self):
        forma = self.forma_cb.get()
        if forma == "Dinheiro":
            self.recebido_ent.config(state="normal")
            # zera campo recebido para digitação
            self.recebido_var.set(brl_format(0.0))
        else:
            self.recebido_var.set(brl_format(0.0))
            self.recebido_ent.config(state="disabled")
            self.troco_var.set(brl_format(0.0))

    def _atualizar_troco(self):
        try:
            recebido = to_float_from_brl(self.recebido_var.get())
            troco = max(0.0, recebido - self.total)
            self.troco_var.set(brl_format(troco))
        except Exception:
            self.troco_var.set(brl_format(0.0))

    # ---------------- finalizar venda ----------------
    def finalizar_venda(self):
        if not self.carrinho:
            messagebox.showwarning("Atenção", "Carrinho vazio.")
            return
        forma = self.forma_cb.get()
        if not forma:
            messagebox.showwarning("Atenção", "Selecione forma de pagamento.")
            return

        recebido = to_float_from_brl(self.recebido_var.get()) if self.forma_cb.get() == "Dinheiro" else None
        troco = to_float_from_brl(self.troco_var.get()) if self.forma_cb.get() == "Dinheiro" else 0.0

        if self.forma_cb.get() == "Dinheiro" and (recebido is None or recebido < self.total):
            messagebox.showwarning("Atenção", "Valor recebido insuficiente.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO vendas (data_venda, operador, total, forma_pagamento, valor_recebido, troco)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.operador, self.total, forma, recebido, troco))
            venda_id = cur.lastrowid

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
                # decrementa estoque se for unidade e existir coluna estoque
                try:
                    if it.get("quantidade") is not None:
                        conn2 = get_connection()
                        c2 = conn2.cursor()
                        c2.execute("SELECT estoque FROM produtos WHERE id=?", (it["produto_id"],))
                        row = c2.fetchone()
                        if row:
                            novo = max(0, int(row[0]) - int(it["quantidade"]))
                            c2.execute("UPDATE produtos SET estoque=? WHERE id=?", (novo, it["produto_id"]))
                            conn2.commit()
                        conn2.close()
                except Exception:
                    pass

            conn.commit()
            conn.close()

            messagebox.showinfo("Venda registrada", f"Venda ID {venda_id} registrada com sucesso!\nTotal: R$ {self.total:.2f}")
            # limpa
            self.carrinho.clear()
            self._refresh_carrinho()
            self._recalcular_total()
            self.forma_cb.set("")
            self.recebido_var.set(brl_format(0.0))
            self.troco_var.set(brl_format(0.0))
            self._carregar_vendas_recentes()
        except sqlite3.Error as e:
            messagebox.showerror("Erro BD", f"Falha ao gravar venda: {e}")

    # ---------------- carregar últimas vendas ----------------
    def _carregar_vendas_recentes(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, data_venda, total, operador FROM vendas ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
            conn.close()
            for r in self.tree_recent.get_children():
                self.tree_recent.delete(r)
            for r in rows:
                self.tree_recent.insert("", "end", values=(r[0], r[1], brl_format(r[2]), r[3]))
        except Exception:
            pass


# execução direta para testes
if __name__ == "__main__":
    app = VendasUI(operador="Teste", role="operador")
    app.mainloop()
