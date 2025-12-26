# ui/estoque_ui.py
import os
import sys
import sqlite3
from datetime import datetime
import logging

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, IntVar

from database.db import get_connection

logging.getLogger(__name__).addHandler(logging.NullHandler())


# ---------------- HELPERS ----------------
def brl_format_float(value):
    try:
        v = float(value or 0)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def ensure_estoque_tables():
    """Garante tabelas de estoque"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque_movimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            produto_nome TEXT,
            tipo_movimento TEXT,
            quantidade INTEGER,
            nota TEXT,
            operador TEXT,
            data_movimento TEXT
        );
    """)
    conn.commit()
    conn.close()


class EstoqueUI(ttk.Frame):
    """Tela de Estoque - Padrão Frame"""
    
    def __init__(self, master, operador_display="Admin", role="admin"):
        super().__init__(master)  # ✅ PRIMEIRO
        self.master = master
        self.pack(fill=BOTH, expand=True)  # ✅ DEPOIS
        
        # Atributos
        self.operador_display = operador_display
        self.display_name = operador_display  # ← Alias para compatibilidade
        self.role = role
        self.operador = operador_display  # ← Usado nos registros
        
        # Cache de produtos
        self.produtos_cache = {}
        self.selected_prod_key = None
        
        # Maximiza janela
        try:
            self.master.state("zoomed")
        except:
            try:
                self.master.attributes("-zoomed", True)
            except:
                pass
        
        # Setup
        ensure_estoque_tables()
        
        # Constrói UI
        self._build_ui()
        
        # Carrega dados
        self._load_produtos()
        self._carregar_historico()

    def _build_ui(self):
        """Constrói interface"""
        
        # Container principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # ========== HEADER ==========
        header_frame = ttk.Frame(main_container, style="Dark.TFrame")
        header_frame.pack(fill=X, padx=0, pady=0)

        ttk.Label(
            header_frame, 
            text="📦 Gestão de Estoque",
            font=("Segoe UI", 18, "bold"), 
            foreground="#FFFFFF"
        ).pack(pady=10)
        
        # Separador
        separator = ttk.Frame(header_frame, height=2, style="success.TFrame")
        separator.pack(fill=X, padx=50, pady=(0, 10))
        
        # Botão voltar
        ttk.Button(
            header_frame, 
            text="🔙 Voltar ao Menu", 
            bootstyle="info", 
            width=20,
            command=self.voltar_dashboard
        ).pack(pady=(0, 10))
        
        # ========== LAYOUT PRINCIPAL ==========
        main = ttk.Frame(main_container)
        main.pack(fill=BOTH, expand=True)

        # Coluna esquerda
        left = ttk.Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        # ========== FORMULÁRIO DE MOVIMENTAÇÃO ==========
        frm = ttk.Labelframe(left, text="Registrar Movimentação", padding=10)
        frm.pack(fill=X, pady=(0, 8))

        # Produto
        ttk.Label(frm, text="Produto:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=W, padx=6, pady=6
        )
        self.combo_produto = ttk.Combobox(frm, values=[], state="readonly", width=50)
        self.combo_produto.grid(row=0, column=1, sticky=W, padx=6)
        self.combo_produto.bind("<<ComboboxSelected>>", lambda e: self._on_produto_selected())

        # Estoque atual
        ttk.Label(frm, text="Estoque Atual:", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky=W, padx=6, pady=6
        )
        self.estoque_atual_var = StringVar(value="0")
        ttk.Label(frm, textvariable=self.estoque_atual_var, 
                 font=("Segoe UI", 12, "bold"),
                 bootstyle="info").grid(row=1, column=1, sticky=W, padx=6)

        # Tipo de movimento
        ttk.Label(frm, text="Tipo:", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky=W, padx=6, pady=6
        )
        self.tipo_cb = ttk.Combobox(frm, values=["Entrada", "Saída"], 
                                    state="readonly", width=20)
        self.tipo_cb.grid(row=2, column=1, sticky=W, padx=6)
        self.tipo_cb.current(0)

        # Quantidade
        ttk.Label(frm, text="Quantidade:", font=("Segoe UI", 10)).grid(
            row=3, column=0, sticky=W, padx=6, pady=6
        )
        self.qtd_var = IntVar(value=1)
        self.qtd_entry = ttk.Entry(frm, textvariable=self.qtd_var, width=12)
        self.qtd_entry.grid(row=3, column=1, sticky=W, padx=6)

        # Nota / Observação
        ttk.Label(frm, text="Nota/Obs:", font=("Segoe UI", 10)).grid(
            row=4, column=0, sticky=W, padx=6, pady=6
        )
        self.nota_var = StringVar()
        self.nota_entry = ttk.Entry(frm, textvariable=self.nota_var, width=50)
        self.nota_entry.grid(row=4, column=1, sticky=W, padx=6)

        # Botões
        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btns, text="💾 Registrar", bootstyle=SUCCESS,
                  command=self.registrar_movimento).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="🔄 Atualizar Produtos", bootstyle=SECONDARY,
                  command=self._load_produtos).pack(side=LEFT, padx=6)

        # ========== LISTA DE PRODUTOS ==========
        prod_frame = ttk.Labelframe(left, text="Produtos (estoque)", padding=8)
        prod_frame.pack(fill=BOTH, expand=True, pady=(8, 0))
        
        cols = ("id", "nome", "tipo", "sabor", "preco", "estoque")
        self.tree_prod = ttk.Treeview(prod_frame, columns=cols, show="headings", height=10)
        
        headings = {
            "id": "ID", "nome": "Nome", "tipo": "Tipo", 
            "sabor": "Sabor", "preco": "Preço", "estoque": "Estoque"
        }
        
        for c in cols:
            self.tree_prod.heading(c, text=headings[c], anchor=CENTER)
            width = 60 if c == "id" else (100 if c == "estoque" else 140)
            self.tree_prod.column(c, anchor="center", width=width)
        
        self.tree_prod.pack(fill=BOTH, expand=True, side=LEFT)
        self.tree_prod.bind("<ButtonRelease-1>", self._on_tree_produto_select)
        
        sb = ttk.Scrollbar(prod_frame, orient="vertical", command=self.tree_prod.yview)
        self.tree_prod.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)

        # ========== COLUNA DIREITA: HISTÓRICO ==========
        right = ttk.Frame(main, width=360)
        right.pack(side=RIGHT, fill=BOTH)

        hist_frame = ttk.Labelframe(right, text="Histórico de Movimentações", padding=8)
        hist_frame.pack(fill=BOTH, expand=True)

        cols2 = ("id", "data", "produto", "tipo", "qtd", "operador", "nota")
        self.tree_hist = ttk.Treeview(hist_frame, columns=cols2, show="headings", height=20)
        
        headings2 = {
            "id": "ID", "data": "Data", "produto": "Produto", 
            "tipo": "Tipo", "qtd": "Qtd", "operador": "Operador", "nota": "Nota"
        }
        
        for c in cols2:
            self.tree_hist.heading(c, text=headings2[c], anchor=CENTER)
            width = 50 if c == "id" else (80 if c == "qtd" else 110)
            self.tree_hist.column(c, anchor="center", width=width)
        
        self.tree_hist.pack(fill=BOTH, expand=True, side=LEFT)
        
        sb2 = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscroll=sb2.set)
        sb2.pack(side=RIGHT, fill=Y)

    # ========== CARREGAMENTO DE DADOS ==========
    def _load_produtos(self):
        """Carrega produtos do banco"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, nome, tipo, sabor, preco, estoque FROM produtos ORDER BY tipo, nome")
            rows = cur.fetchall()
            conn.close()
            
            self.produtos_cache.clear()
            
            # Limpa tree
            for r in self.tree_prod.get_children():
                self.tree_prod.delete(r)
            
            # Popula
            for r in rows:
                pid, nome, tipo, sabor, preco, estoque = r
                key = f"{nome} (id:{pid})"
                
                self.produtos_cache[key] = {
                    "id": pid, 
                    "nome": nome, 
                    "tipo": tipo, 
                    "sabor": sabor, 
                    "preco": float(preco or 0.0),
                    "estoque": int(estoque or 0)
                }
                
                self.tree_prod.insert("", "end", values=(
                    pid, nome, tipo, sabor, 
                    brl_format_float(preco), 
                    estoque or 0
                ))
            
            # Popula combo
            keys = list(self.produtos_cache.keys())
            self.combo_produto['values'] = keys
            self.combo_produto.set("")
            self.estoque_atual_var.set("0")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar produtos: {e}")

    def _on_produto_selected(self):
        """Atualiza estoque atual ao selecionar produto"""
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
        """Seleciona produto no combo ao clicar na tree"""
        sel = self.tree_prod.selection()
        if not sel:
            return
        
        vals = self.tree_prod.item(sel[0])["values"]
        pid = vals[0]
        
        # Busca chave no cache
        key = next((k for k, v in self.produtos_cache.items() if v["id"] == pid), None)
        if key:
            self.combo_produto.set(key)
            self._on_produto_selected()

    # ========== REGISTRO DE MOVIMENTAÇÃO ==========
    def registrar_movimento(self):
        """Registra movimentação de estoque"""
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

        # Calcula novo estoque
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            estoque_atual = int(info.get("estoque", 0))
            
            if tipo == "entrada":
                novo = estoque_atual + qtd
            else:  # saída
                novo = estoque_atual - qtd
                if novo < 0:
                    if not messagebox.askyesno("Confirmar", 
                        "Saída deixará estoque negativo. Confirmar?"):
                        conn.close()
                        return

            # Atualiza produtos
            cur.execute("UPDATE produtos SET estoque=? WHERE id=?", (novo, produto_id))
            
            # Registra movimento
            cur.execute("""
                INSERT INTO estoque_movimentos 
                (produto_id, produto_nome, tipo_movimento, quantidade, nota, operador, data_movimento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (produto_id, produto_nome, tipo, qtd, nota, self.operador, 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", f"Movimentação registrada. Estoque atual: {novo}")
            
            # Atualiza cache
            self.produtos_cache[key]["estoque"] = novo
            self.estoque_atual_var.set(str(novo))
            
            # Recarrega
            self._load_produtos()
            self._carregar_historico()
            
            # Alerta estoque baixo
            if novo <= 5:
                messagebox.showwarning("Estoque baixo", 
                    f"O produto '{produto_nome}' está com estoque baixo: {novo}")
            
            # Limpa campos
            self.qtd_var.set(1)
            self.nota_var.set("")
            
        except sqlite3.Error as e:
            messagebox.showerror("Erro BD", f"Falha ao registrar movimentação: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _carregar_historico(self, limit=100):
        """Carrega histórico de movimentações"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, data_movimento, produto_nome, tipo_movimento, 
                       quantidade, operador, nota 
                FROM estoque_movimentos 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            conn.close()
            
            # Limpa tree
            for r in self.tree_hist.get_children():
                self.tree_hist.delete(r)
            
            # Popula
            for row in rows:
                self.tree_hist.insert("", "end", values=row)
                
        except Exception as e:
            logging.error(f"Erro ao carregar histórico: {e}")

    def voltar_dashboard(self):
        """Volta para dashboard - SEM subprocess"""
        self.destroy()
        from ui.dashboard_ui import DashboardUI
        DashboardUI(master=self.master, 
                    display_name=self.display_name, 
                    role=self.role)