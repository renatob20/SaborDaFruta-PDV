# ui/bater_ponto_ui.py — VERSÃO AVANÇADA
"""
UI: Bater Ponto
- Registrar entrada/saída de operadores
- Histórico com filtros avançados
- Export CSV e PDF
"""
import os
import sys
import logging
from datetime import datetime, timedelta

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, filedialog
import pandas as pd

# garante imports relativos
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.bater_ponto_db import (
    ensure_tables,
    listar_operadores,
    registrar_batida,
    listar_batidas_periodo,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())


# ========== AJUSTE: Classe modificada para Window em vez de Toplevel ==========
class BaterPontoUI(ttk.Window):
    """Janela independente para registro de ponto."""

    def __init__(self, operador_display=None, role="operador"):
        super().__init__(themename="superhero")
        
        # ---- Maximiza a Janela (Comportamento padrão para Windows) ----
        try:
            self.state("zoomed")
        except Exception:
            # Fallback para sistemas Windows onde 'zoomed' não está disponível
            # ou em casos muito específicos.
            self.attributes("-zoomed", True)
        
        
        self.operador_display = operador_display
        self.role = role

        self.title("⏰ Registro de Ponto")
        self.geometry("1100x700")
        self.minsize(1000, 600)

        # vars
        self.funcionario_var = StringVar()
        self.filtro_operador_var = StringVar(value="Todos")
        self._operadores = []
        
        # Variáveis para filtro de período
        self.data_inicio = None
        self.data_fim = None

        # inicializa DB
        try:
            ensure_tables()
        except Exception as e:
            logging.exception("Erro ao inicializar tabelas:")

        # constrói UI
        self._build_ui()
        # carrega dados iniciais
        self._carregar_operadores()

    def _build_ui(self):
        """Constrói o layout da janela."""
        pad = 10

        # ===== HEADER =====
        header = ttk.Label(self, text="⏰ Registro de Ponto", font=("Segoe UI", 14, "bold"))
        header.pack(pady=5)

        # ===== Frame Top (Registro de Ponto) =====
        frm_registro = ttk.Labelframe(self, text="🕐 Registrar Ponto", padding=10)
        frm_registro.pack(fill="x", padx=pad, pady=(5, 10))

        ttk.Label(frm_registro, text="Operador:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.func_cb = ttk.Combobox(
            frm_registro,
            textvariable=self.funcionario_var,
            width=30,
            state="readonly"
        )
        self.func_cb.pack(side="left", padx=(0, 10))

        ttk.Button(
            frm_registro,
            text="✅ Registrar Ponto",
            bootstyle=SUCCESS,
            command=self._registrar_ponto
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            frm_registro,
            text="🔄 Atualizar",
            bootstyle=INFO,
            command=self._carregar_operadores
        ).pack(side="left", padx=(0, 5))

        # ===== FILTROS AVANÇADOS =====
        filtros_frame = ttk.Labelframe(self, text="🔍 Filtros Avançados", padding=15)
        filtros_frame.pack(fill=X, padx=pad, pady=(0, 10))

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
        
        ttk.Button(btn_rapidos, text="🗓 Este Mês", bootstyle="info-outline", width=14,
                   command=self.filtro_mes_atual).pack(side=LEFT, padx=3)

        # Linha 2: Período personalizado + Filtro por operador
        personalizado = ttk.Frame(filtros_frame)
        personalizado.pack(fill=X, pady=(5, 0))

        ttk.Label(personalizado, text="Período Personalizado:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 10))

        ttk.Label(personalizado, text="De:").pack(side=LEFT, padx=(10, 5))
        # ========== CALENDÁRIO DATA INÍCIO ==========
        self.entry_inicio = ttk.DateEntry(personalizado, bootstyle="primary", dateformat="%d/%m/%Y")
        self.entry_inicio.pack(side=LEFT, padx=5)

        ttk.Label(personalizado, text="Até:").pack(side=LEFT, padx=(15, 5))
        # ========== CALENDÁRIO DATA FIM ==========
        self.entry_fim = ttk.DateEntry(personalizado, bootstyle="primary", dateformat="%d/%m/%Y")
        self.entry_fim.pack(side=LEFT, padx=5)

        ttk.Button(personalizado, text="🔎 Aplicar Filtro", bootstyle="success", width=15,
                   command=self.aplicar_filtro_personalizado).pack(side=LEFT, padx=15)

        # Filtro por operador
        ttk.Label(personalizado, text="Operador:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(20, 5))
        self.filtro_operador_cb = ttk.Combobox(
            personalizado,
            textvariable=self.filtro_operador_var,
            width=20,
            state="readonly"
        )
        self.filtro_operador_cb.pack(side=LEFT, padx=5)
        self.filtro_operador_cb.bind("<<ComboboxSelected>>", lambda e: self._carregar_historico())

        ttk.Button(personalizado, text="🔄 Limpar", bootstyle="secondary", width=12,
                   command=self.limpar_filtros).pack(side=LEFT, padx=3)

        # ===== Frame Botões de Exportação =====
        frm_export = ttk.Frame(self)
        frm_export.pack(fill=X, padx=pad, pady=(0, 5))

        ttk.Label(frm_export, text="📥 Exportar:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 10))

        ttk.Button(
            frm_export,
            text="💾 Exportar CSV",
            bootstyle=INFO,
            width=18,
            command=self._exportar_csv
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            frm_export,
            text="📄 Exportar PDF",
            bootstyle=WARNING,
            width=18,
            command=self._exportar_pdf
        ).pack(side=LEFT, padx=5)

        # ===== Frame Histórico (Treeview) =====
        frm_hist = ttk.Labelframe(self, text="📋 Histórico de Batidas", padding=10)
        frm_hist.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        cols = ("id", "operador", "tipo", "timestamp")
        self.tree = ttk.Treeview(
            frm_hist,
            columns=cols,
            show="headings",
            height=18
        )

        # config colunas
        self.tree.heading("id", text="ID", anchor="center")
        self.tree.heading("operador", text="Operador", anchor="center")
        self.tree.heading("tipo", text="Tipo", anchor="center")
        self.tree.heading("timestamp", text="Data/Hora", anchor="center")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("operador", width=250, anchor="center")
        self.tree.column("tipo", width=100, anchor="center")
        self.tree.column("timestamp", width=200, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        # scrollbar
        sb = ttk.Scrollbar(frm_hist, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def _carregar_operadores(self):
        """Carrega lista de operadores do banco e popula os Comboboxes."""
        logging.debug("_carregar_operadores() chamado")
        try:
            self._operadores = listar_operadores()
            logging.debug(f"Carregados {len(self._operadores)} operadores")

            valores = [display for (_id, display, _u) in self._operadores]
            
            # Combobox de registro
            self.func_cb['values'] = valores

            # Combobox de filtro (com opção "Todos")
            valores_filtro = ["Todos"] + valores
            self.filtro_operador_cb['values'] = valores_filtro

            # tenta selecionar o operador passado no construtor
            if self.operador_display and self.operador_display in valores:
                self.funcionario_var.set(self.operador_display)
            elif valores:
                self.funcionario_var.set(valores[0])
            
            # Define "Todos" como padrão no filtro
            self.filtro_operador_var.set("Todos")
            
        except Exception as e:
            logging.exception("Erro ao carregar operadores:")
            messagebox.showerror("Erro", f"Não foi possível carregar operadores: {e}")

    def _registrar_ponto(self):
        """Registra uma batida (entrada ou saída)."""
        logging.debug("_registrar_ponto() chamado")

        nome_sel = (self.funcionario_var.get() or "").strip()
        if not nome_sel:
            messagebox.showwarning("Atenção", "Selecione um operador.")
            return

        # busca o id do operador
        match = next((op for op in self._operadores if op[1] == nome_sel), None)
        if not match:
            messagebox.showerror("Erro", f"Operador '{nome_sel}' não encontrado.")
            return

        funcionario_id = match[0]
        logging.debug(f"Operador selecionado: id={funcionario_id} nome={nome_sel}")

        # decide tipo (entrada ou saída) alternando a partir do histórico
        try:
            rows = listar_batidas_periodo(periodo="diario", funcionario_id=funcionario_id)
            last = rows[0] if rows else None

            if last and last[2].lower() == "entrada":
                tipo = "saida"
            else:
                tipo = "entrada"

            logging.debug(f"Tipo escolhido: {tipo} (baseado no último: {last[2] if last else 'nenhum'})")
        except Exception as e:
            logging.debug(f"Erro ao determinar tipo: {e} — assumindo 'entrada'")
            tipo = "entrada"

        try:
            bid = registrar_batida(funcionario_id, tipo)
            messagebox.showinfo(
                "Sucesso",
                f"Batida registrada!\n\nOperador: {nome_sel}\nTipo: {tipo.upper()}\nID: {bid}"
            )
            self._carregar_historico()
        except Exception as e:
            logging.exception("Erro ao registrar batida:")
            messagebox.showerror("Erro", f"Falha ao registrar batida: {e}")

    # ========== FILTROS RÁPIDOS ==========
    def filtro_hoje(self):
        hoje = datetime.now()
        self.data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_historico()

    def filtro_7_dias(self):
        hoje = datetime.now()
        self.data_inicio = (hoje - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_historico()

    def filtro_30_dias(self):
        hoje = datetime.now()
        self.data_inicio = (hoje - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_historico()

    def filtro_mes_atual(self):
        hoje = datetime.now()
        self.data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        self._carregar_historico()

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
            
            self._carregar_historico()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao aplicar filtro: {str(e)}")

    def limpar_filtros(self):
        self.data_inicio = None
        self.data_fim = None
        self.filtro_operador_var.set("Todos")
        for r in self.tree.get_children():
            self.tree.delete(r)

    def _carregar_historico(self):
        """Carrega histórico de batidas no Treeview com filtros aplicados."""
        logging.debug("_carregar_historico() chamado")

        # limpa tree
        for r in self.tree.get_children():
            self.tree.delete(r)

        try:
            from database.db import get_connection
            conn = get_connection()
            
            # Monta a query com filtros
            query = """
                SELECT pb.id, u.display_name, pb.tipo, pb.timestamp
                FROM ponto_batidas pb
                JOIN usuarios u ON pb.funcionario_id = u.id
                WHERE 1=1
            """
            params = []
            
            # Filtro por período
            if self.data_inicio and self.data_fim:
                inicio_str = self.data_inicio.strftime("%Y-%m-%d %H:%M:%S")
                fim_str = self.data_fim.strftime("%Y-%m-%d %H:%M:%S")
                query += " AND pb.timestamp BETWEEN ? AND ?"
                params.extend([inicio_str, fim_str])
            
            # Filtro por operador
            operador_filtro = self.filtro_operador_var.get()
            if operador_filtro and operador_filtro != "Todos":
                query += " AND u.display_name = ?"
                params.append(operador_filtro)
            
            query += " ORDER BY pb.timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            logging.debug(f"Carregadas {len(df)} batidas")

            for _, row in df.iterrows():
                # ========== FORMATAÇÃO DA DATA (SEM MICROSEGUNDOS) ==========
                timestamp = row.get("timestamp", "")
                try:
                    if timestamp:
                        # Remove microsegundos
                        data_str = str(timestamp).split('.')[0]
                        data_obj = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                        timestamp_formatado = data_obj.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp_formatado = ""
                except:
                    timestamp_formatado = str(timestamp).split('.')[0] if timestamp else ""
                # ===========================================================
                
                self.tree.insert("", "end", values=(
                    row.get("id"),
                    row.get("display_name"),
                    row.get("tipo", "").upper(),
                    timestamp_formatado
                ))
                
        except Exception as e:
            logging.exception("Erro ao carregar histórico:")
            messagebox.showerror("Erro", f"Não foi possível carregar histórico: {e}")

    def _exportar_csv(self):
        """Exporta histórico para arquivo CSV."""
        logging.debug("_exportar_csv() chamado")

        try:
            from database.db import get_connection
            conn = get_connection()
            
            # Monta a query com filtros
            query = """
                SELECT pb.id, u.display_name as Operador, pb.tipo as Tipo, pb.timestamp as DataHora
                FROM ponto_batidas pb
                JOIN usuarios u ON pb.funcionario_id = u.id
                WHERE 1=1
            """
            params = []
            
            # Filtro por período
            if self.data_inicio and self.data_fim:
                inicio_str = self.data_inicio.strftime("%Y-%m-%d %H:%M:%S")
                fim_str = self.data_fim.strftime("%Y-%m-%d %H:%M:%S")
                query += " AND pb.timestamp BETWEEN ? AND ?"
                params.extend([inicio_str, fim_str])
            
            # Filtro por operador
            operador_filtro = self.filtro_operador_var.get()
            if operador_filtro and operador_filtro != "Todos":
                query += " AND u.display_name = ?"
                params.append(operador_filtro)
            
            query += " ORDER BY pb.timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                messagebox.showwarning("Aviso", "Não há dados para exportar!")
                return
            
            # Remove microsegundos das datas
            df['DataHora'] = df['DataHora'].apply(lambda x: str(x).split('.')[0] if x else "")
            
            fn = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*")],
                initialfile=f"ponto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            if not fn:
                return

            df.to_csv(fn, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Sucesso", f"Arquivo exportado com sucesso!\n{len(df)} registros salvos.\n\n{fn}")
            logging.debug(f"Arquivo CSV exportado: {fn}")
            
        except Exception as e:
            logging.exception("Erro ao exportar CSV:")
            messagebox.showerror("Erro", f"Falha ao exportar: {e}")

    def _exportar_pdf(self):
        """Exporta histórico para arquivo PDF."""
        logging.debug("_exportar_pdf() chamado")

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            
            from database.db import get_connection
            conn = get_connection()
            
            # Monta a query com filtros
            query = """
                SELECT pb.id, u.display_name, pb.tipo, pb.timestamp
                FROM ponto_batidas pb
                JOIN usuarios u ON pb.funcionario_id = u.id
                WHERE 1=1
            """
            params = []
            
            # Filtro por período
            if self.data_inicio and self.data_fim:
                inicio_str = self.data_inicio.strftime("%Y-%m-%d %H:%M:%S")
                fim_str = self.data_fim.strftime("%Y-%m-%d %H:%M:%S")
                query += " AND pb.timestamp BETWEEN ? AND ?"
                params.extend([inicio_str, fim_str])
            
            # Filtro por operador
            operador_filtro = self.filtro_operador_var.get()
            if operador_filtro and operador_filtro != "Todos":
                query += " AND u.display_name = ?"
                params.append(operador_filtro)
            
            query += " ORDER BY pb.timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                messagebox.showwarning("Aviso", "Não há dados para exportar!")
                return
            
            fn = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf"), ("All Files", "*")],
                initialfile=f"ponto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            if not fn:
                return

            # Criar PDF
            doc = SimpleDocTemplate(fn, pagesize=landscape(A4))
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            
            # Título
            titulo = Paragraph("<b>Relatório de Ponto</b>", styles['Title'])
            elements.append(titulo)
            elements.append(Spacer(1, 0.5*cm))
            
            # Informações do filtro
            info_filtro = f"<b>Período:</b> "
            if self.data_inicio and self.data_fim:
                info_filtro += f"{self.data_inicio.strftime('%d/%m/%Y')} até {self.data_fim.strftime('%d/%m/%Y')}"
            else:
                info_filtro += "Todos os registros"
            
            info_filtro += f"<br/><b>Operador:</b> {operador_filtro if operador_filtro else 'Todos'}"
            info_filtro += f"<br/><b>Total de registros:</b> {len(df)}"
            info_filtro += f"<br/><b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            
            elements.append(Paragraph(info_filtro, styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
            
            # Preparar dados da tabela
            data = [['ID', 'Operador', 'Tipo', 'Data/Hora']]
            
            for _, row in df.iterrows():
                # Remove microsegundos
                timestamp = str(row['timestamp']).split('.')[0] if row['timestamp'] else ""
                data.append([
                    str(row['id']),
                    str(row['display_name']),
                    str(row['tipo']).upper(),
                    timestamp
                ])
            
            # Criar tabela
            table = Table(data, colWidths=[2*cm, 6*cm, 3*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(table)
            
            # Gerar PDF
            doc.build(elements)
            
            messagebox.showinfo("Sucesso", f"PDF exportado com sucesso!\n{len(df)} registros salvos.\n\n{fn}")
            logging.debug(f"Arquivo PDF exportado: {fn}")
            
        except ImportError:
            messagebox.showerror("Erro", "Biblioteca ReportLab não instalada!\n\nInstale com: pip install reportlab")
        except Exception as e:
            logging.exception("Erro ao exportar PDF:")
            messagebox.showerror("Erro", f"Falha ao exportar PDF: {e}")


# ========== EXECUÇÃO DIRETA (AJUSTADO - SEM JANELA EXTRA) ==========
# Execução direta para teste
if __name__ == "__main__":
    import sys
    
    # obtém argumentos passados via linha de comando (do dashboard)
    operador_display = sys.argv[1] if len(sys.argv) > 1 else "Operador"
    role = sys.argv[2] if len(sys.argv) > 2 else "operador"
    
    # Cria janela principal diretamente (sem root invisível)
    app = BaterPontoUI(operador_display=operador_display, role=role)
    app.mainloop()