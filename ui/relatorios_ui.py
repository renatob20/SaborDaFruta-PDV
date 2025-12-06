# ---------- PARTE 1: Imports + Helpers ----------
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import subprocess

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, DoubleVar, IntVar, filedialog

#### verificar conecção com o banco ###########
from database.products_db import get_connection

def brl(value):
    if value is None:
        return "0,00"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
################################################




class RelatoriosUI(ttk.Window):
    def __init__(self, display_name="Admin", role="admin"):
        super().__init__(themename="superhero")
        self.title("📊 Relatórios - Açaiteria o Sabor da Fruta")
        self.geometry("900x600")
        self.minsize(900,600)
        
        self.display_name = display_name
        self.role = role
        
        
        self._build_ui()
# #### verificar a chamada para a função #self._carregar_produtos()
      

    def _build_ui(self):
        header = ttk.Label(self, text="Relatórios de Vendas", font=("Segoe UI", 16, "bold"))
        header.pack(pady=10)
        
        frm = ttk.Frame(self)
        frm.pack(fill=X, padx=12)

        options = ttk.Labelframe(frm, text="Selecione o relatório", padding=10)
        options.pack(fill=X)

        btns = ttk.Frame(self)
        btns.pack(fill=X, pady=8, padx=6)

        ttk.Button(btns, text="📅 Vendas de Hoje", bootstyle=PRIMARY, width=25,
           command=self.relatorio_diario).pack(side=LEFT, padx=8, pady=5)

        ttk.Button(btns, text="📆 Últimos 7 dias", bootstyle=PRIMARY, width=25,
           command=self.relatorio_semanal).pack(side=LEFT, padx=8, pady=5)

        ttk.Button(btns, text="🗓 Vendas do Mês", bootstyle=PRIMARY, width=25,
           command=self.relatorio_mensal).pack(side=LEFT, padx=8, pady=5)

        ttk.Button(btns, text="🍦 Produtos mais vendidos", bootstyle=WARNING, width=25,
           command=self.relatorio_produtos).pack(side=LEFT, padx=8, pady=5)

        ttk.Button(btns, text="⬇ Exportar para Excel", bootstyle=INFO, width=25,
           command=self.exportar_excel).pack(side=LEFT, padx=8, pady=5)

        # tabela
        frame_table = ttk.Frame(frm)
        frame_table.pack(fill=BOTH, expand=True, pady=10)

        cols = ("id","data","produto","qtd","peso","subtotal","operador")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings")

        headers = {
            "id":"ID","data":"Data","produto":"Produto",
            "qtd":"Qtd","peso":"Peso","subtotal":"Subtotal","operador":"Operador"
        }

        for c in cols:
            self.tree.heading(c, text=headers[c], anchor="center")
            self.tree.column(c, anchor="center", width=120)

        # pack tree and scrollbar inside frame_table
        self.tree.pack(fill=BOTH, expand=True, side=LEFT)
        scroll = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.pack(side=RIGHT, fill=Y)

        # footer com botão Voltar alinhado à direita, abaixo da tabela
        footer = ttk.Frame(frm)
        footer.pack(fill=X, pady=(8,15))
        btn_voltar = ttk.Button(footer, text="🔙 Voltar", bootstyle=INFO, command=self.voltar_dashboard)
        btn_voltar.pack(side=RIGHT, padx=10)


    # ---------- PARTE 3: Lógica dos relatórios ----------
    def _load(self, query, params=()):
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        self._update_table(df)
        return df

    def _update_table(self, df):
        for r in self.tree.get_children():
            self.tree.delete(r)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(
                row.get("id"),
                row.get("data_venda"),
                row.get("produto_nome"),
                row.get("quantidade"),
                row.get("peso_kg"),
                brl(row.get("subtotal")),
                row.get("operador"),
            ))

    def relatorio_diario(self):
        hoje = datetime.now().strftime("%Y-%m-%d") + "%"
        self._load("""
            SELECT v.id, v.data_venda, i.produto_nome, i.quantidade, i.peso_kg, i.subtotal, v.operador
            FROM vendas v
            JOIN venda_items i ON v.id = i.venda_id
            WHERE v.data_venda LIKE ?
            ORDER BY v.id DESC
        """, (hoje,))

    def relatorio_semanal(self):
        data_limite = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        self._load("""
            SELECT v.id, v.data_venda, i.produto_nome, i.quantidade, i.peso_kg, i.subtotal, v.operador
            FROM vendas v
            JOIN venda_items i ON v.id = i.venda_id
            WHERE v.data_venda >= ?
            ORDER BY v.id DESC
        """, (data_limite,))

    def relatorio_mensal(self):
        mes = datetime.now().strftime("%Y-%m")
        self._load("""
            SELECT v.id, v.data_venda, i.produto_nome, i.quantidade, i.peso_kg, i.subtotal, v.operador
            FROM vendas v
            JOIN venda_items i ON v.id = i.venda_id
            WHERE v.data_venda LIKE ?
            ORDER BY v.id DESC
        """, (mes + "%",))

    def relatorio_produtos(self):
        self._load("""
            SELECT 
                i.id,
                i.produto_nome,
                SUM(i.quantidade) AS total_qtd,
                SUM(i.peso_kg) AS total_peso,
                SUM(i.subtotal) AS total_vendido,
                v.operador,
                v.data_venda
            FROM venda_items i
            JOIN vendas v ON v.id = i.venda_id
            GROUP BY i.produto_nome
            ORDER BY total_vendido DESC
        """)

    def exportar_excel(self):
        conn = get_connection()
        df = pd.read_sql_query("""
            SELECT v.id, v.data_venda, i.produto_nome, i.quantidade, i.peso_kg, i.subtotal, v.operador
            FROM vendas v
            JOIN venda_items i ON v.id = i.venda_id
        """, conn)
        conn.close()

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )

        if not path:
            return

        df.to_excel(path, index=False)
        messagebox.showinfo("Exportado", "Relatório exportado com sucesso!")

    # --------- Navegação / utilitários ----------
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

if __name__ == "__main__":
    app = RelatoriosUI("Admin", "admin")
    app.mainloop()



