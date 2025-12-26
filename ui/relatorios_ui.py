# ui/relatorios_ui.py
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog

from database.db import get_connection


def brl(value):
    """Formata valor para BRL"""
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_peso(peso):
    """Formata peso, tratando None"""
    if peso is None or pd.isna(peso):
        return "-"
    try:
        return f"{float(peso):.3f}"
    except:
        return "-"


class RelatoriosUI(ttk.Frame):
    """Tela de Relatórios - Padrão Frame"""
    
    def __init__(self, master, display_name="Admin", role="admin"):
        super().__init__(master)  # ✅ PRIMEIRO
        self.master = master
        self.pack(fill=BOTH, expand=True)  # ✅ DEPOIS
        
        # Atributos
        self.display_name = display_name
        self.role = role
        
        # Variáveis para filtro
        self.data_inicio = None
        self.data_fim = None
        
        # Controle de modo de visualização
        self.modo_atual = "vendas"  # "vendas" ou "produtos"
        
        # Maximiza janela
        try:
            self.master.state("zoomed")
        except:
            try:
                self.master.attributes("-zoomed", True)
            except:
                pass
        
        # Constrói UI
        self._build_ui()

    def voltar_dashboard(self):
        """Volta para dashboard - SEM subprocess"""
        self.destroy()
        from ui.dashboard_ui import DashboardUI
        DashboardUI(master=self.master, 
                    display_name=self.display_name, 
                    role=self.role)

    def _build_ui(self):
        """Constrói interface"""
        
        # Container principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True, padx=12, pady=12)
        
        # ========== HEADER ==========
        header_frame = ttk.Frame(main_container, style="Dark.TFrame")
        header_frame.pack(fill=X, padx=0, pady=0)
        
        ttk.Label(
            header_frame, 
            text="📊 Relatórios de Vendas",
            font=("Segoe UI", 18, "bold"), 
            foreground="#FFFFFF"
        ).pack(pady=10)
        
        # Separador
        separator = ttk.Frame(header_frame, height=2, style="success.TFrame")
        separator.pack(fill=X, padx=50, pady=(0, 10))
        
        # # Botão voltar
        # ttk.Button(
        #     header_frame, 
        #     text="🔙 Voltar ao Menu", 
        #     bootstyle="info", 
        #     width=20,
        #     command=self.voltar_dashboard
        # ).pack(pady=(0, 10))
        
        # ========== FILTROS AVANÇADOS ==========
        filtros_frame = ttk.Labelframe(main_container, text="🔍 Filtros Avançados", padding=15)
        filtros_frame.pack(fill=X, pady=(0, 10))

        # Linha 1: Botões rápidos
        btn_rapidos = ttk.Frame(filtros_frame)
        btn_rapidos.pack(fill=X, pady=(0, 10))

        ttk.Label(btn_rapidos, text="Períodos Rápidos:", 
                 font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 10))

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

        ttk.Label(personalizado, text="Período Personalizado:", 
                 font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 10))

        ttk.Label(personalizado, text="De:").pack(side=LEFT, padx=(10, 5))
        self.entry_inicio = ttk.DateEntry(personalizado, bootstyle="primary", dateformat="%d/%m/%Y")
        self.entry_inicio.pack(side=LEFT, padx=5)

        ttk.Label(personalizado, text="Até:").pack(side=LEFT, padx=(15, 5))
        self.entry_fim = ttk.DateEntry(personalizado, bootstyle="primary", dateformat="%d/%m/%Y")
        self.entry_fim.pack(side=LEFT, padx=5)

        ttk.Button(personalizado, text="🔎 Aplicar Filtro", bootstyle="success", width=15,
                   command=self.aplicar_filtro_personalizado).pack(side=LEFT, padx=15)
        
        ttk.Button(personalizado, text="🔄 Limpar", bootstyle="secondary", width=12,
                   command=self.limpar_filtros).pack(side=LEFT, padx=3)

        # ========== BOTÕES DE RELATÓRIOS +  botão voltar==========
        options = ttk.Labelframe(main_container, text="📊 Visualizações e Exportação", padding=10)
        options.pack(fill=X, pady=(0, 10))

        btns = ttk.Frame(options)
        btns.pack(fill=X)

        ttk.Button(btns, text="📋 Ver Detalhes das Vendas", bootstyle=SUCCESS, width=25,
                   command=self.mostrar_vendas).pack(side=LEFT, padx=8, pady=5)

        ttk.Button(btns, text="🍦 Produtos mais vendidos", bootstyle=WARNING, width=25,
                   command=self.relatorio_produtos).pack(side=LEFT, padx=8, pady=5)

        ttk.Button(btns, text="⬇ Exportar para Excel", bootstyle=INFO, width=25,
                   command=self.exportar_excel).pack(side=LEFT, padx=8, pady=5)
        
        ttk.Button(btns, text="🔙 Voltar ao Menu", bootstyle=INFO, width=25,
                   command=self.voltar_dashboard).pack(side=RIGHT, padx=8, pady=5)

        # ========== RESUMO DO PERÍODO ==========
        self.resumo_frame = ttk.Labelframe(main_container, text="📈 Resumo do Período", padding=15)
        self.resumo_frame.pack(fill=X, pady=(0, 10))

        # Grid para os cards
        resumo_grid = ttk.Frame(self.resumo_frame)
        resumo_grid.pack(fill=X)

        # Card 1: Total de Vendas
        card1 = ttk.Frame(resumo_grid, bootstyle="primary")
        card1.grid(row=0, column=0, padx=8, pady=5, sticky="ew")
        ttk.Label(card1, text="💰 Total de Vendas", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_total_vendas = ttk.Label(card1, text="R$ 0,00", 
                                         font=("Segoe UI", 16, "bold"), 
                                         bootstyle="inverse-primary")
        self.lbl_total_vendas.pack()

        # Card 2: Número de Vendas
        card2 = ttk.Frame(resumo_grid, bootstyle="success")
        card2.grid(row=0, column=1, padx=8, pady=5, sticky="ew")
        ttk.Label(card2, text="🛒 Número de Vendas", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_num_vendas = ttk.Label(card2, text="0", 
                                       font=("Segoe UI", 16, "bold"), 
                                       bootstyle="inverse-success")
        self.lbl_num_vendas.pack()

        # Card 3: Ticket Médio
        card3 = ttk.Frame(resumo_grid, bootstyle="info")
        card3.grid(row=0, column=2, padx=8, pady=5, sticky="ew")
        ttk.Label(card3, text="📊 Ticket Médio", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_ticket_medio = ttk.Label(card3, text="R$ 0,00", 
                                         font=("Segoe UI", 16, "bold"), 
                                         bootstyle="inverse-info")
        self.lbl_ticket_medio.pack()

        for i in range(3):
            resumo_grid.columnconfigure(i, weight=1)

        # Linha 2: Formas de pagamento
        pagamentos_frame = ttk.Frame(self.resumo_frame)
        pagamentos_frame.pack(fill=X, pady=(10, 0))

        ttk.Label(pagamentos_frame, text="💳 Por Forma de Pagamento:", 
                 font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 5))

        pag_grid = ttk.Frame(pagamentos_frame)
        pag_grid.pack(fill=X)

        # Cards de pagamento
        pag1 = ttk.Frame(pag_grid)
        pag1.grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Label(pag1, text="💵 Dinheiro:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_dinheiro = ttk.Label(pag1, text="R$ 0,00", 
                                     font=("Segoe UI", 10, "bold"), 
                                     bootstyle="success")
        self.lbl_dinheiro.pack(side=LEFT, padx=5)

        pag2 = ttk.Frame(pag_grid)
        pag2.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Label(pag2, text="💳 Crédito:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_credito = ttk.Label(pag2, text="R$ 0,00", 
                                    font=("Segoe UI", 10, "bold"), 
                                    bootstyle="info")
        self.lbl_credito.pack(side=LEFT, padx=5)

        pag3 = ttk.Frame(pag_grid)
        pag3.grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Label(pag3, text="💳 Débito:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_debito = ttk.Label(pag3, text="R$ 0,00", 
                                   font=("Segoe UI", 10, "bold"), 
                                   bootstyle="warning")
        self.lbl_debito.pack(side=LEFT, padx=5)

        pag4 = ttk.Frame(pag_grid)
        pag4.grid(row=0, column=3, padx=5, sticky="ew")
        ttk.Label(pag4, text="📱 Pix:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_pix = ttk.Label(pag4, text="R$ 0,00", 
                                font=("Segoe UI", 10, "bold"), 
                                bootstyle="primary")
        self.lbl_pix.pack(side=LEFT, padx=5)

        for i in range(4):
            pag_grid.columnconfigure(i, weight=1)

        # ========== TABELA DE VENDAS ==========
        self.frame_table = ttk.Labelframe(main_container, text="📋 Detalhes das Vendas", padding=10)
        self.frame_table.pack(fill=BOTH, expand=True, pady=5)

        cols = ("id", "data", "produto", "qtd", "peso", "subtotal", "operador")
        self.tree = ttk.Treeview(self.frame_table, columns=cols, show="headings", height=12)

        headers = {
            "id": "ID", "data": "Data", "produto": "Produto",
            "qtd": "Qtd", "peso": "Peso (KG)", "subtotal": "Subtotal", "operador": "Operador"
        }

        for c in cols:
            self.tree.heading(c, text=headers[c], anchor="center")
            if c == "data":
                self.tree.column(c, anchor="center", width=150)
            else:
                self.tree.column(c, anchor="center", width=120)

        self.tree.pack(fill=BOTH, expand=True, side=LEFT)
        
        scroll = ttk.Scrollbar(self.frame_table, orient="vertical", command=self.tree.yview)
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
        self.modo_atual = "vendas"
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._atualizar_resumo(0, 0, 0, 0, 0, 0, 0)
        self.frame_table.config(text="📋 Detalhes das Vendas")

    # ========== CARREGAMENTO DE DADOS ==========
    def _carregar_relatorio(self):
        """Carrega relatório de vendas detalhadas"""
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

        # Define modo atual
        self.modo_atual = "vendas"
        self.frame_table.config(text="📋 Detalhes das Vendas")

        # Atualiza tabela
        self._update_table_vendas(df_items)

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
        """Atualiza os cards de resumo"""
        self.lbl_num_vendas.config(text=str(num_vendas))
        self.lbl_total_vendas.config(text=brl(total_vendas))
        self.lbl_ticket_medio.config(text=brl(ticket_medio))
        self.lbl_dinheiro.config(text=brl(dinheiro))
        self.lbl_credito.config(text=brl(credito))
        self.lbl_debito.config(text=brl(debito))
        self.lbl_pix.config(text=brl(pix))

    def _update_table_vendas(self, df):
        """Atualiza tabela com dados de vendas"""
        for r in self.tree.get_children():
            self.tree.delete(r)

        for _, row in df.iterrows():
            # Formata data sem microsegundos
            data_venda = row.get("data_venda", "")
            try:
                if data_venda:
                    data_str = str(data_venda).split('.')[0]
                    data_obj = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                    data_formatada = data_obj.strftime("%d/%m/%Y %H:%M")
                else:
                    data_formatada = ""
            except:
                data_formatada = str(data_venda).split('.')[0] if data_venda else ""
            
            # Formata peso (trata None)
            peso = formatar_peso(row.get("peso_kg"))
            
            self.tree.insert("", "end", values=(
                row.get("id"),
                data_formatada,
                row.get("produto_nome"),
                row.get("quantidade"),
                peso,
                brl(row.get("subtotal")),
                row.get("operador"),
            ))

    # ========== VISUALIZAÇÕES ==========
    def mostrar_vendas(self):
        """Volta para visualização de vendas detalhadas"""
        if not self.data_inicio or not self.data_fim:
            messagebox.showwarning("Aviso", "Selecione um período primeiro!")
            return
        
        self.modo_atual = "vendas"
        self._carregar_relatorio()

    def relatorio_produtos(self):
        """Mostra relatório de produtos mais vendidos"""
        if not self.data_inicio or not self.data_fim:
            messagebox.showwarning("Aviso", "Selecione um período primeiro!")
            return

        inicio_str = self.data_inicio.strftime("%Y-%m-%d %H:%M:%S")
        fim_str = self.data_fim.strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        df = pd.read_sql_query("""
            SELECT 
                i.produto_nome,
                SUM(i.quantidade) AS total_qtd,
                SUM(COALESCE(i.peso_kg, 0)) AS total_peso,
                SUM(i.subtotal) AS total_vendido
            FROM venda_items i
            JOIN vendas v ON v.id = i.venda_id
            WHERE v.data_venda BETWEEN ? AND ?
            GROUP BY i.produto_nome
            ORDER BY total_vendido DESC
        """, conn, params=(inicio_str, fim_str))
        conn.close()

        # Define modo atual
        self.modo_atual = "produtos"
        self.frame_table.config(text="🍦 Produtos Mais Vendidos")

        # Limpa tabela
        for r in self.tree.get_children():
            self.tree.delete(r)

        # Popula tabela
        for idx, row in df.iterrows():
            # Formata peso (soma total)
            total_peso = row['total_peso']
            peso_formatado = formatar_peso(total_peso) if total_peso > 0 else "-"
            
            self.tree.insert("", "end", values=(
                idx + 1,  # Ranking
                "",  # Data (não se aplica)
                row['produto_nome'],
                int(row['total_qtd']),
                peso_formatado,
                brl(row['total_vendido']),
                ""  # Operador (não se aplica)
            ))

        if df.empty:
            messagebox.showinfo("Info", "Nenhum produto encontrado no período selecionado.")

    def exportar_excel(self):
        """Exporta dados para Excel"""
        if not self.data_inicio or not self.data_fim:
            messagebox.showwarning("Aviso", "Selecione um período primeiro!")
            return

        inicio_str = self.data_inicio.strftime("%Y-%m-%d %H:%M:%S")
        fim_str = self.data_fim.strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        
        # Exporta vendas detalhadas
        df_vendas = pd.read_sql_query("""
            SELECT v.id, v.data_venda, i.produto_nome, i.quantidade, i.peso_kg, i.subtotal, v.operador
            FROM vendas v
            JOIN venda_items i ON v.id = i.venda_id
            WHERE v.data_venda BETWEEN ? AND ?
            ORDER BY v.data_venda DESC
        """, conn, params=(inicio_str, fim_str))
        
        # Exporta produtos mais vendidos
        df_produtos = pd.read_sql_query("""
            SELECT 
                i.produto_nome,
                SUM(i.quantidade) AS total_quantidade,
                SUM(COALESCE(i.peso_kg, 0)) AS total_peso_kg,
                SUM(i.subtotal) AS total_vendido
            FROM venda_items i
            JOIN vendas v ON v.id = i.venda_id
            WHERE v.data_venda BETWEEN ? AND ?
            GROUP BY i.produto_nome
            ORDER BY total_vendido DESC
        """, conn, params=(inicio_str, fim_str))
        
        conn.close()

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"relatorio_{self.data_inicio.strftime('%Y%m%d')}_{self.data_fim.strftime('%Y%m%d')}.xlsx"
        )

        if not path:
            return

        # Cria arquivo Excel com múltiplas abas
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df_vendas.to_excel(writer, sheet_name='Vendas Detalhadas', index=False)
            df_produtos.to_excel(writer, sheet_name='Produtos Mais Vendidos', index=False)

        messagebox.showinfo("Exportado", 
            f"Relatório exportado com sucesso!\n\n"
            f"• Vendas: {len(df_vendas)} registros\n"
            f"• Produtos: {len(df_produtos)} itens\n\n"
            f"Arquivo: {path}")


# ========== EXECUÇÃO DIRETA PARA TESTE ==========
if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    root.title("Relatórios de Vendas")
    app = RelatoriosUI(root, display_name="Admin", role="admin")
    root.mainloop()