# ui/estoque_ui.py
import os
import sys
import sqlite3
from datetime import datetime
import subprocess

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

  
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, IntVar, DoubleVar



# tenta usar get_connection do seu módulo database/products_db.py ou database/db.py
try:
    from database.products_db import get_connection
except Exception:
    try:
        from database.db import get_connection
    except Exception:
        def get_connection():
            db_path = os.path.join("database", "acaiteria.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return sqlite3.connect(db_path)

# ---------------- util helpers ----------------
def brl_format_float(value):
    try:
        v = float(value or 0)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"

# ---------------- garante tabelas de estoque ----------------
def ensure_estoque_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque_movimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            produto_nome TEXT,
            tipo_movimento TEXT,     -- 'entrada' ou 'saida'
            quantidade INTEGER,
            nota TEXT,
            operador TEXT,
            data_movimento TEXT
        );
    """)
    # garante coluna 'estoque' na tabela produtos (se não existir, não tenta alterar estrutura complexa)
    # assumimos que a tabela produtos já existe com coluna estoque; se não existir, o app já tem scripts de init_db
    conn.commit()
    conn.close()

# ---------------- UI: EstoqueUI ----------------
class EstoqueUI(ttk.Window):
    def __init__(self, display_name="Admin", role="admin"):
        super().__init__(themename="superhero")
        self.title("📦 Gestão de Estoque - Açaiteria")
        self.geometry("900x600")
        self.minsize(900,600)
        
        self.display_name = display_name
        self.role = role

        
        self._build_ui()

        # dados locais
        self.produtos_cache = {}  # chave (display) -> dict {id,nome,tipo,sabor,preco,estoque}
        self.selected_prod_key = None

        ensure_estoque_tables()
        self._build_ui()
        self._load_produtos()
        self._carregar_historico()

    def _build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill=X)
        ttk.Label(header, text="Gestão de Estoque", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        #ttk.Label(header, text=f"Admin: {self.admin}", font=("Segoe UI", 10)).pack(side=RIGHT)

        main = ttk.Frame(self, padding=10)
        main.pack(fill=BOTH, expand=True)

        left = ttk.Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,8))

        frm = ttk.Labelframe(left, text="Registrar Movimentação", padding=10)
        frm.pack(fill=X, pady=(0,8))

        # Produto
        ttk.Label(frm, text="Produto:").grid(row=0, column=0, sticky=W, padx=6, pady=6)
        self.combo_produto = ttk.Combobox(frm, values=[], state="readonly", width=50)
        self.combo_produto.grid(row=0, column=1, sticky=W, padx=6)
        self.combo_produto.bind("<<ComboboxSelected>>", lambda e: self._on_produto_selected())

        # Estoque atual (informativo)
        ttk.Label(frm, text="Estoque Atual:").grid(row=1, column=0, sticky=W, padx=6, pady=6)
        self.estoque_atual_var = StringVar(value="0")
        self.estoque_atual_lbl = ttk.Label(frm, textvariable=self.estoque_atual_var)
        self.estoque_atual_lbl.grid(row=1, column=1, sticky=W, padx=6)

        # Tipo de movimento
        ttk.Label(frm, text="Tipo:").grid(row=2, column=0, sticky=W, padx=6, pady=6)
        self.tipo_cb = ttk.Combobox(frm, values=["Entrada", "Saída"], state="readonly", width=20)
        self.tipo_cb.grid(row=2, column=1, sticky=W, padx=6)
        self.tipo_cb.current(0)

        # Quantidade
        ttk.Label(frm, text="Quantidade:").grid(row=3, column=0, sticky=W, padx=6, pady=6)
        self.qtd_var = IntVar(value=1)
        self.qtd_entry = ttk.Entry(frm, textvariable=self.qtd_var, width=12)
        self.qtd_entry.grid(row=3, column=1, sticky=W, padx=6)

        # Nota / Observação
        ttk.Label(frm, text="Nota/Obs:").grid(row=4, column=0, sticky=W, padx=6, pady=6)
        self.nota_var = StringVar()
        self.nota_entry = ttk.Entry(frm, textvariable=self.nota_var, width=50)
        self.nota_entry.grid(row=4, column=1, sticky=W, padx=6)

        # Botões
        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="💾 Registrar", bootstyle=SUCCESS, command=self.registrar_movimento).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="🔄 Atualizar Produtos", bootstyle=SECONDARY, command=self._load_produtos).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="🔙 Voltar", bootstyle=INFO, command=self.voltar_dashboard).pack(side=RIGHT, padx=6)

        # Lista produtos (informativa)
        prod_frame = ttk.Labelframe(left, text="Produtos (estoque)", padding=8)
        prod_frame.pack(fill=BOTH, expand=True, pady=(8,0))
        cols = ("id","nome","tipo","sabor","preco","estoque")
        self.tree_prod = ttk.Treeview(prod_frame, columns=cols, show="headings")
        headings = {"id":"ID","nome":"Nome","tipo":"Tipo","sabor":"Sabor","preco":"Preço","estoque":"Estoque"}
        for c in cols:
            self.tree_prod.heading(c, text=headings[c])
            self.tree_prod.column(c, anchor="center", width=100 if c=="id" else 140)
        self.tree_prod.pack(fill=BOTH, expand=True, side=LEFT)
        sb = ttk.Scrollbar(prod_frame, orient="vertical", command=self.tree_prod.yview)
        self.tree_prod.configure(yscroll=sb.set); sb.pack(side=RIGHT, fill=Y)
        self.tree_prod.bind("<ButtonRelease-1>", self._on_tree_produto_select)

        # Right: histórico
        right = ttk.Frame(main, width=360)
        right.pack(side=RIGHT, fill=BOTH)

        hist_frame = ttk.Labelframe(right, text="Histórico de Movimentações", padding=8)
        hist_frame.pack(fill=BOTH, expand=True)

        cols2 = ("id","data","produto","tipo","qtd","operador","nota")
        self.tree_hist = ttk.Treeview(hist_frame, columns=cols2, show="headings")
        headings2 = {"id":"ID","data":"Data","produto":"Produto","tipo":"Tipo","qtd":"Qtd","operador":"Operador","nota":"Nota"}
        for c in cols2:
            self.tree_hist.heading(c, text=headings2[c])
            self.tree_hist.column(c, anchor="center", width=110 if c=="id" else 140)
        self.tree_hist.pack(fill=BOTH, expand=True, side=LEFT)
        sb2 = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscroll=sb2.set); sb2.pack(side=RIGHT, fill=Y)

    # ---------------- carrega produtos ----------------
    def _load_produtos(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            # esperamos colunas id, nome, tipo, sabor, preco, estoque na tabela produtos
            cur.execute("SELECT id, nome, tipo, sabor, preco, estoque FROM produtos ORDER BY tipo, nome")
            rows = cur.fetchall()
            conn.close()
            self.produtos_cache.clear()
            # popula tree_prod
            for r in self.tree_prod.get_children():
                self.tree_prod.delete(r)
            for r in rows:
                pid, nome, tipo, sabor, preco, estoque = r
                self.produtos_cache[f"{nome} (id:{pid})"] = {
                    "id": pid, "nome": nome, "tipo": tipo, "sabor": sabor, "preco": float(preco or 0.0),
                    "estoque": int(estoque or 0)
                }
                self.tree_prod.insert("", "end", values=(pid, nome, tipo, sabor, brl_format_float(preco), estoque or 0))
            # popula combo_produto com exibição amigável (nome (id))
            keys = list(self.produtos_cache.keys())
            self.combo_produto['values'] = keys
            self.combo_produto.set("")  # limpa seleção
            self.estoque_atual_var.set("0")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar produtos: {e}")

    def _on_produto_selected(self):
        key = self.combo_produto.get()
        if not key:
            self.estoque_atual_var.set("0")
            return
        info = self.produtos_cache.get(key)
        if not info:
            self.estoque_atual_var.set("0")
            return
        self.selected_prod_key = key
        self.estoque_atual_var.set(str(info.get("estoque", 0)))

    def _on_tree_produto_select(self, event=None):
        sel = self.tree_prod.selection()
        if not sel:
            return
        vals = self.tree_prod.item(sel[0])["values"]
        pid = vals[0]
        # tentar selecionar no combo
        key = next((k for k,v in self.produtos_cache.items() if v["id"] == pid), None)
        if key:
            self.combo_produto.set(key)
            self._on_produto_selected()

    # ---------------- registrar movimentação ----------------
    def registrar_movimento(self):
        key = self.combo_produto.get()
        if not key:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        info = self.produtos_cache.get(key)
        if not info:
            messagebox.showerror("Erro", "Produto não encontrado.")
            return

        tipo = (self.tipo_cb.get() or "Entrada").strip().lower()
        try:
            qtd = int(self.qtd_var.get())
        except Exception:
            messagebox.showwarning("Atenção", "Quantidade inválida.")
            return
        if qtd <= 0:
            messagebox.showwarning("Atenção", "Quantidade deve ser maior que zero.")
            return

        nota = (self.nota_var.get() or "").strip()
        produto_id = info["id"]
        produto_nome = info["nome"]

        # atualiza estoque no DB
        try:
            conn = get_connection()
            cur = conn.cursor()
            if tipo == "entrada":
                novo = int(info.get("estoque", 0)) + qtd
            else:
                novo = int(info.get("estoque", 0)) - qtd
                if novo < 0:
                    # bloqueia saída que deixa negativo — você pode ajustar para permitir
                    if not messagebox.askyesno("Confirmar", "Saída deixará estoque negativo. Confirmar?"):
                        conn.close()
                        return

            # atualiza tabela produtos
            cur.execute("UPDATE produtos SET estoque=? WHERE id=?", (novo, produto_id))
            # insere movimento no histórico
            cur.execute("""
                INSERT INTO estoque_movimentos (produto_id, produto_nome, tipo_movimento, quantidade, nota, operador, data_movimento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (produto_id, produto_nome, tipo, qtd, nota, self.operador, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", f"Movimentação registrada. Estoque atual: {novo}")
            # atualiza cache local e UI
            self.produtos_cache[key]["estoque"] = novo
            self.estoque_atual_var.set(str(novo))
            # atualiza lista de produtos e histórico
            self._load_produtos()
            self._carregar_historico()
            # alerta se estoque baixo (por exemplo <=5 unidades)
            if novo <= 5:
                messagebox.showwarning("Estoque baixo", f"O produto '{produto_nome}' está com estoque baixo: {novo}")
            # limpar campos
            self.qtd_var.set(1)
            self.nota_var.set("")
        except sqlite3.Error as e:
            messagebox.showerror("Erro BD", f"Falha ao registrar movimentação: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    # ---------------- carregar histórico ----------------
    def _carregar_historico(self, limit=100):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, data_movimento, produto_nome, tipo_movimento, quantidade, operador, nota FROM estoque_movimentos ORDER BY id DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            conn.close()
            for r in self.tree_hist.get_children():
                self.tree_hist.delete(r)
            for row in rows:
                self.tree_hist.insert("", "end", values=row)
        except Exception:
            pass

    # ---------------- voltar ao dashboard ----------------
    def voltar_dashboard(self):
        """Ação ao clicar em Voltar — fecha esta janela (ajuste se houver dashboard)."""
        dashboard_script = os.path.join(ROOT, "ui", "dashboard_ui.py")
        try:
            subprocess.Popen([sys.executable, dashboard_script, self.display_name, self.role], close_fds=True)
        except Exception:
           # fallback simples caso Popen falhe, tenta chamar via os.system
            os.system(f'"{sys.executable}" "{dashboard_script}" "{self.display_name}" "{self.role}"') 
        # fecha apenas esta janela; o novo processo continua rodando
          
        self.destroy()
# execução direta para testes
if __name__ == "__main__":
    app = EstoqueUI("Admin", "admin")
    app.mainloop()
