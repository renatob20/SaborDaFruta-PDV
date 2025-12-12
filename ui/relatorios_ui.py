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
from ttkbootstrap.dialogs import Messagebox

#### verificar conexão com o banco ###########
from database.db import get_connection

def brl(value):
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
################################################


class RelatoriosUI(ttk.Window):
    def __init__(self, display_name="Admin", role="admin"):
        super().__init__(themename="superhero")
        self.title("📊 Relatórios - Açaiteria o Sabor da Fruta")
        self.geometry("1100x700")
        self.minsize(1100, 700)
        
        self.display_name = display_name
        self.role = role
        
        # Variáveis para o relatório avançado
        self.data_inicio = None
        self.data_fim = None
        
        self._build_ui()

    def _build_ui(self):
        # ========== HEADER COM BOTÃO VOLTAR (ATUALIZADO) ==========
        # Movido o botão para o topo junto com o título para melhor visibilidade
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=5, padx=12)
        
        ttk.Label(header_frame, text="Relatórios de Vendas", font=("Segoe UI", 14, "bold")).pack(side=LEFT)
        
        ttk.Button(header_frame, text="🔙 Voltar ao Dashboard", bootstyle="info", width=20, 
                   command=self.voltar_dashboard).pack(side=RIGHT, padx=5)
        # ===========================================================
        
        frm = ttk.Frame(self)
        frm.pack(fill=BOTH, expand=True, padx=12, pady=3)

        # ========== FRAME DE FILTROS AVANÇADOS ==========
        filtros_frame = ttk.Labelframe(frm, text="🔍 Filtros Avançados", padding=15)
        filtros_frame.pack(fill=X, pady=(0, 10))

        # Linha 1: Botões rápidos
        btn_rapidos = ttk.Frame(filtros_frame)
        btn_rapidos.pack(fill=X, pady=(0, 10))

        ttk.Label(btn_rapidos, text="Períodos Rápidos:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 10))

        ttk.Button(btn_rapidos, text="📅 Hoje", bootstyle="success-outline", width=12,
                   command=self.filtro_hoje).pack(side=LEFT, padx=3)
        
        ttk.Button(btn_rapidos, text="📆 Últimos 7 dias", bootstyle="primary-outline", width=15,
                   command=self.filtro_7_dias).pack(side=LEFT, padx=3)
        
        ttk.Button(btn_rapidos, text="📆 Últimos 30 dias", bootstyle="primary-outline", width=15,
                   command=self.filtro_30_dias).pack(side=LEFT, padx=3)
        
        ttk.Button(btn_rapidos, text="📅 Últimos 3 meses", bootstyle="info-outline", width=16,
                   command=self.filtro_3_meses).pack(side=LEFT, padx=3)
        
        ttk.Button(btn_rapidos, text="📅 Últimos 6 meses", bootstyle="info-outline", width=16,
                   command=self.filtro_6_meses).pack(side=LEFT, padx=3)
        
        ttk.Button(btn_rapidos, text="📅 Último 1 ano", bootstyle="warning-outline", width=14,
                   command=self.filtro_1_ano).pack(side=LEFT, padx=3)

        # Linha 2: Período personalizado
        personalizado = ttk.Frame(filtros_frame)
        personalizado.pack(fill=X, pady=(5, 0))

        ttk.Label(personalizado, text="Período Personalizado:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 10))

        ttk.Label(personalizado, text="De:").pack(side=LEFT, padx=(10, 5))
        # ========== CALENDÁRIO DATA INÍCIO (ATUALIZADO - FORMATO CORRIGIDO) ==========
        self.entry_inicio = ttk.DateEntry(personalizado, bootstyle="primary", dateformat="%d/%m/%Y")
        self.entry_inicio.pack(side=LEFT, padx=5)
        # ==============================================================================

        ttk.Label(personalizado, text="Até:").pack(side=LEFT, padx=(15, 5))
        # ========== CALENDÁRIO DATA FIM (ATUALIZADO - FORMATO CORRIGIDO) ==========
        self.entry_fim = ttk.DateEntry(personalizado, bootstyle="primary", dateformat="%d/%m/%Y")
        self.entry_fim.pack(side=LEFT, padx=5)
        # ===========================================================================

        ttk.Button(personalizado, text="🔎 Aplicar Filtro", bootstyle="success", width=15,
                   command=self.aplicar_filtro_personalizado).pack(side=LEFT, padx=15)
        
        ttk.Button(personalizado, text="🔄 Limpar", bootstyle="secondary", width=12,
                   command=self.limpar_filtros).pack(side=LEFT, padx=3)

        # ========== BOTÕES DE RELATÓRIOS ESPECÍFICOS ==========
        options = ttk.Labelframe(frm, text="📊 Outros Relatórios", padding=10)
        options.pack(fill=X, pady=(0, 10))

        btns = ttk.Frame(options)
        btns.pack(fill=X)

        ttk.Button(btns, text="🍦 Produtos mais vendidos", bootstyle=WARNING, width=25,
                   command=self.relatorio_produtos).pack(side=LEFT, padx=8, pady=5)

        ttk.Button(btns, text="⬇ Exportar para Excel", bootstyle=INFO, width=25,
                   command=self.exportar_excel).pack(side=LEFT, padx=8, pady=5)

        # ========== RESUMO DO PERÍODO ==========
        self.resumo_frame = ttk.Labelframe(frm, text="📈 Resumo do Período", padding=15)
        self.resumo_frame.pack(fill=X, pady=(0, 10))

        # Grid para os cards de resumo
        resumo_grid = ttk.Frame(self.resumo_frame)
        resumo_grid.pack(fill=X)

        # Card 1: Total de Vendas
        card1 = ttk.Frame(resumo_grid, bootstyle="primary")
        card1.grid(row=0, column=0, padx=8, pady=5, sticky="ew")
        ttk.Label(card1, text="💰 Total de Vendas", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_total_vendas = ttk.Label(card1, text="R$ 0,00", font=("Segoe UI", 16, "bold"), bootstyle="inverse-primary")
        self.lbl_total_vendas.pack()

        # Card 2: Número de Vendas
        card2 = ttk.Frame(resumo_grid, bootstyle="success")
        card2.grid(row=0, column=1, padx=8, pady=5, sticky="ew")
        ttk.Label(card2, text="🛒 Número de Vendas", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_num_vendas = ttk.Label(card2, text="0", font=("Segoe UI", 16, "bold"), bootstyle="inverse-success")
        self.lbl_num_vendas.pack()

        # Card 3: Ticket Médio
        card3 = ttk.Frame(resumo_grid, bootstyle="info")
        card3.grid(row=0, column=2, padx=8, pady=5, sticky="ew")
        ttk.Label(card3, text="📊 Ticket Médio", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_ticket_medio = ttk.Label(card3, text="R$ 0,00", font=("Segoe UI", 16, "bold"), bootstyle="inverse-info")
        self.lbl_ticket_medio.pack()

        # Configurar grid para expandir igualmente
        for i in range(3):
            resumo_grid.columnconfigure(i, weight=1)

        # Linha 2: Formas de pagamento
        pagamentos_frame = ttk.Frame(self.resumo_frame)
        pagamentos_frame.pack(fill=X, pady=(10, 0))

        ttk.Label(pagamentos_frame, text="💳 Por Forma de Pagamento:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 5))

        pag_grid = ttk.Frame(pagamentos_frame)
        pag_grid.pack(fill=X)

        # Dinheiro
        pag1 = ttk.Frame(pag_grid)
        pag1.grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Label(pag1, text="💵 Dinheiro:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_dinheiro = ttk.Label(pag1, text="R$ 0,00", font=("Segoe UI", 10, "bold"), bootstyle="success")
        self.lbl_dinheiro.pack(side=LEFT, padx=5)

        # Crédito
        pag2 = ttk.Frame(pag_grid)
        pag2.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Label(pag2, text="💳 Crédito:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_credito = ttk.Label(pag2, text="R$ 0,00", font=("Segoe UI", 10, "bold"), bootstyle="info")
        self.lbl_credito.pack(side=LEFT, padx=5)

        # Débito
        pag3 = ttk.Frame(pag_grid)
        pag3.grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Label(pag3, text="💳 Débito:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_debito = ttk.Label(pag3, text="R$ 0,00", font=("Segoe UI", 10, "bold"), bootstyle="warning")
        self.lbl_debito.pack(side=LEFT, padx=5)

        # Pix
        pag4 = ttk.Frame(pag_grid)
        pag4.grid(row=0, column=3, padx=5, sticky="ew")
        ttk.Label(pag4, text="📱 Pix:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_pix = ttk.Label(pag4, text="R$ 0,00", font=("Segoe UI", 10, "bold"), bootstyle="primary")
        self.lbl_pix.pack(side=LEFT, padx=5)

        for i in range(4):
            pag_grid.columnconfigure(i, weight=1)

        # ========== TABELA DE VENDAS ==========
        frame_table = ttk.Frame(frm)
        frame_table.pack(fill=BOTH, expand=True, pady=5)

        cols = ("id", "data", "produto", "qtd", "peso", "subtotal", "operador")
        self.tree = ttk.Treeview(frame_table, columns=cols, show="headings", height=12)

        headers = {
            "id": "ID", "data": "Data", "produto": "Produto",
            "qtd": "Qtd", "peso": "Peso", "subtotal": "Subtotal", "operador": "Operador"
        }

        for c in cols:
            self.tree.heading(c, text=headers[c], anchor="center")
            if c == "data":
                self.tree.column(c, anchor="center", width=150)  # Mais largo para data com hora
            else:
                self.tree.column(c, anchor="center", width=120)

        self.tree.pack(fill=BOTH, expand=True, side=LEFT)
        scroll = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.pack(side=RIGHT, fill=Y)

    # ========== FILTROS RÁPIDOS ==========
    def filtro_hoje(self):
        hoje = datetime.now()
        self.data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_relatorio()

    def filtro_7_dias(self):
        hoje = datetime.now()
        self.data_inicio = (hoje - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_relatorio()

    def filtro_30_dias(self):
        hoje = datetime.now()
        self.data_inicio = (hoje - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_relatorio()

    def filtro_3_meses(self):
        hoje = datetime.now()
        self.data_inicio = (hoje - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_relatorio()

    def filtro_6_meses(self):
        hoje = datetime.now()
        self.data_inicio = (hoje - timedelta(days=180)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_relatorio()

    def filtro_1_ano(self):
        hoje = datetime.now()
        self.data_inicio = (hoje - timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_relatorio()

    def aplicar_filtro_personalizado(self):
        try:
            # Pega as datas dos DateEntry
            inicio = self.entry_inicio.entry.get()
            fim = self.entry_fim.entry.get()
            
            self.data_inicio = datetime.strptime(inicio, "%d/%m/%Y").replace(hour=0, minute=0, second=0)
            self.data_fim = datetime.strptime(fim, "%d/%m/%Y").replace(hour=23, minute=59, second=59)
            
            if self.data_inicio > self.data_fim:
                messagebox.showerror("Erro", "A data inicial não pode ser maior que a data final!")
                return
            
            self._carregar_relatorio()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao aplicar filtro: {str(e)}")

    def limpar_filtros(self):
        self.data_inicio = None
        self.data_fim = None
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._atualizar_resumo(0, 0, 0, 0, 0, 0, 0)

    # ========== CARREGAMENTO DE DADOS ==========
    def _carregar_relatorio(self):
        if not self.data_inicio or not self.data_fim:
            messagebox.showwarning("Aviso", "Selecione um período primeiro!")
            return

        inicio_str = self.data_inicio.strftime("%Y-%m-%d %H:%M:%S")
        fim_str = self.data_fim.strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        
        # Query para items
        df_items = pd.read_sql_query("""
            SELECT v.id, v.data_venda, i.produto_nome, i.quantidade, i.peso_kg, i.subtotal, v.operador
            FROM vendas v
            JOIN venda_items i ON v.id = i.venda_id
            WHERE v.data_venda BETWEEN ? AND ?
            ORDER BY v.data_venda DESC
        """, conn, params=(inicio_str, fim_str))

        # Query para resumo
        resumo = pd.read_sql_query("""
            SELECT 
                COUNT(DISTINCT v.id) as num_vendas,
                COALESCE(SUM(v.total), 0) as total_vendas,
                COALESCE(SUM(CASE WHEN v.forma_pagamento = 'Dinheiro' THEN v.total ELSE 0 END), 0) as total_dinheiro,
                COALESCE(SUM(CASE WHEN v.forma_pagamento = 'Crédito' THEN v.total ELSE 0 END), 0) as total_credito,
                COALESCE(SUM(CASE WHEN v.forma_pagamento = 'Débito' THEN v.total ELSE 0 END), 0) as total_debito,
                COALESCE(SUM(CASE WHEN v.forma_pagamento = 'Pix' THEN v.total ELSE 0 END), 0) as total_pix
            FROM vendas v
            WHERE v.data_venda BETWEEN ? AND ?
        """, conn, params=(inicio_str, fim_str))

        conn.close()

        # Atualiza tabela
        self._update_table(df_items)

        # Atualiza resumo
        if not resumo.empty:
            row = resumo.iloc[0]
            num_vendas = int(row['num_vendas'])
            total_vendas = float(row['total_vendas'])
            ticket_medio = total_vendas / num_vendas if num_vendas > 0 else 0
            
            self._atualizar_resumo(
                num_vendas,
                total_vendas,
                ticket_medio,
                float(row['total_dinheiro']),
                float(row['total_credito']),
                float(row['total_debito']),
                float(row['total_pix'])
            )

    def _atualizar_resumo(self, num_vendas, total_vendas, ticket_medio, dinheiro, credito, debito, pix):
        self.lbl_num_vendas.config(text=str(num_vendas))
        self.lbl_total_vendas.config(text=brl(total_vendas))
        self.lbl_ticket_medio.config(text=brl(ticket_medio))
        self.lbl_dinheiro.config(text=brl(dinheiro))
        self.lbl_credito.config(text=brl(credito))
        self.lbl_debito.config(text=brl(debito))
        self.lbl_pix.config(text=brl(pix))

    def _update_table(self, df):
        for r in self.tree.get_children():
            self.tree.delete(r)

        for _, row in df.iterrows():
            # ========== FORMATAÇÃO DA DATA (ATUALIZADO) ==========
            # Remove os microsegundos e exibe apenas AAAA-MM-DD HH:MM:SS
            data_venda = row.get("data_venda", "")
            try:
                if data_venda:
                    # Remove microsegundos (tudo após o ponto)
                    data_str = str(data_venda).split('.')[0]
                    data_obj = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                    data_formatada = data_obj.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    data_formatada = ""
            except:
                # Se falhar, tenta remover apenas o que está após o ponto
                data_formatada = str(data_venda).split('.')[0] if data_venda else ""
            # ======================================================
            
            self.tree.insert("", "end", values=(
                row.get("id"),
                data_formatada,
                row.get("produto_nome"),
                row.get("quantidade"),
                row.get("peso_kg"),
                brl(row.get("subtotal")),
                row.get("operador"),
            ))

    # ========== OUTROS RELATÓRIOS ==========
    def relatorio_produtos(self):
        conn = get_connection()
        df = pd.read_sql_query("""
            SELECT 
                i.produto_nome,
                SUM(i.quantidade) AS total_qtd,
                SUM(i.peso_kg) AS total_peso,
                SUM(i.subtotal) AS total_vendido
            FROM venda_items i
            JOIN vendas v ON v.id = i.venda_id
            GROUP BY i.produto_nome
            ORDER BY total_vendido DESC
        """, conn)
        conn.close()

        # Limpa e mostra na tabela
        for r in self.tree.get_children():
            self.tree.delete(r)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(
                "",
                "",
                row['produto_nome'],
                int(row['total_qtd']),
                f"{row['total_peso']:.2f}",
                brl(row['total_vendido']),
                ""
            ))

    def exportar_excel(self):
        if not self.data_inicio or not self.data_fim:
            messagebox.showwarning("Aviso", "Selecione um período primeiro!")
            return

        inicio_str = self.data_inicio.strftime("%Y-%m-%d %H:%M:%S")
        fim_str = self.data_fim.strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        df = pd.read_sql_query("""
            SELECT v.id, v.data_venda, i.produto_nome, i.quantidade, i.peso_kg, i.subtotal, v.operador
            FROM vendas v
            JOIN venda_items i ON v.id = i.venda_id
            WHERE v.data_venda BETWEEN ? AND ?
            ORDER BY v.data_venda DESC
        """, conn, params=(inicio_str, fim_str))
        conn.close()

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"relatorio_{self.data_inicio.strftime('%Y%m%d')}_{self.data_fim.strftime('%Y%m%d')}.xlsx"
        )

        if not path:
            return

        df.to_excel(path, index=False)
        messagebox.showinfo("Exportado", f"Relatório exportado com sucesso!\n{len(df)} registros salvos.")

    # ========== NAVEGAÇÃO ==========
    def voltar_dashboard(self):
        dashboard_script = os.path.join(ROOT, "ui", "dashboard_ui.py")
        try:
            subprocess.Popen([sys.executable, dashboard_script, self.display_name, self.role], close_fds=True)
        except Exception:
            os.system(f'"{sys.executable}" "{dashboard_script}" "{self.display_name}" "{self.role}"')
        self.destroy()


if __name__ == "__main__":
    app = RelatoriosUI("Admin", "admin")
    app.mainloop()