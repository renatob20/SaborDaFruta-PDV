from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from controllers.sales_controller import registrar_venda
import sqlite3
import os 
from datetime import datetime

DB_PATH = os.path.join("database", "acaiteria.db")

def get_connection():
    return sqlite3.connect(DB_PATH)


class TelaVendas(QWidget):
    def __init__(self, operador, tipo):
        super().__init__()
        self.operador = operador
        self.tipo = tipo
        self.setWindowTitle(f"📦 PDV - Açaiteria o Sabor da Fruta | Usuário: {self.operador} ({self.tipo})")
        self.setGeometry(300, 150, 950, 600)

        self.initUI()

    def initUI(self):
        # ======== CAMPOS DO FORMULÁRIO =========
        self.tipo_produto = QComboBox()
        self.tipo_produto.addItems(["Picolé", "Sorvete a Granel", "Copo 300ml", "Outros"])

        self.sabor = QLineEdit()
        self.sabor.setPlaceholderText("Ex: Morango, Açaí com Banana...")

        self.quantidade = QLineEdit()
        self.quantidade.setPlaceholderText("Kg ou Unidades")

        self.valor_unit = QLineEdit()
        self.valor_unit.setPlaceholderText("Ex: 1.00, 5.50...")

        self.forma_pagamento = QComboBox()
        self.forma_pagamento.addItems(["Pix", "Crédito", "Débito", "Dinheiro"])

        self.observacoes = QLineEdit()
        self.observacoes.setPlaceholderText("Observações (opcional)")

        # ======== BOTÕES =========
        self.btn_registrar = QPushButton("Registrar Venda")
        self.btn_registrar.clicked.connect(self.registrar_venda)

        # Botão de exclusão (restrito)
        self.btn_excluir = QPushButton("Excluir Venda")
        self.btn_excluir.clicked.connect(self.excluir_venda)

        # Controle de acesso: apenas admin pode excluir
        if self.tipo != "admin":
            self.btn_excluir.setEnabled(False)
            self.btn_excluir.setToolTip("Somente administradores podem excluir vendas")

        # ======== FILTROS =========
        self.filtro_tipo = QComboBox()
        self.filtro_tipo.addItems(["Todos", "Picolé", "Sorvete a Granel", "Copo 300ml", "Outros"])

        self.filtro_pagamento = QComboBox()
        self.filtro_pagamento.addItems(["Todos", "Pix", "Crédito", "Débito", "Dinheiro"])

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.clicked.connect(self.carregar_vendas)

        # ======== TABELA =========
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(9)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Data", "Produto", "Sabor", "Qtd", "Valor Unit", "Total", "Pagamento", "Operador"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ======== LAYOUT =========
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Tipo:"))
        form_layout.addWidget(self.tipo_produto)
        form_layout.addWidget(QLabel("Sabor:"))
        form_layout.addWidget(self.sabor)
        form_layout.addWidget(QLabel("Qtd:"))
        form_layout.addWidget(self.quantidade)
        form_layout.addWidget(QLabel("R$/unid:"))
        form_layout.addWidget(self.valor_unit)
        form_layout.addWidget(QLabel("Pgto:"))
        form_layout.addWidget(self.forma_pagamento)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.observacoes)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_registrar)
        btn_layout.addWidget(self.btn_excluir)
        layout.addLayout(btn_layout)

        # Filtros
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Tipo:"))
        filtro_layout.addWidget(self.filtro_tipo)
        filtro_layout.addWidget(QLabel("Pagamento:"))
        filtro_layout.addWidget(self.filtro_pagamento)
        filtro_layout.addWidget(self.btn_filtrar)
        layout.addLayout(filtro_layout)

        layout.addWidget(self.tabela)
        self.setLayout(layout)

        # Carregar vendas existentes
        self.carregar_vendas()

    # ================= MÉTODOS =================

    def registrar_venda(self):
        try:
            tipo = self.tipo_produto.currentText()
            sabor = self.sabor.text().strip()
            qtd = float(self.quantidade.text())
            valor_unit = float(self.valor_unit.text())
            forma_pagamento = self.forma_pagamento.currentText()
            obs = self.observacoes.text().strip()

            registrar_venda(tipo, sabor, qtd, valor_unit, forma_pagamento, self.operador, obs)
            QMessageBox.information(self, "Sucesso", "Venda registrada com sucesso!")

            self.sabor.clear()
            self.quantidade.clear()
            self.valor_unit.clear()
            self.observacoes.clear()
            self.carregar_vendas()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao registrar venda: {str(e)}")

    def carregar_vendas(self):
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, data_venda, tipo_produto, sabor, quantidade,
                   valor_unit, valor_total, forma_pagamento, operador
            FROM vendas WHERE 1=1
        """
        params = []

        if self.filtro_tipo.currentText() != "Todos":
            query += " AND tipo_produto = ?"
            params.append(self.filtro_tipo.currentText())

        if self.filtro_pagamento.currentText() != "Todos":
            query += " AND forma_pagamento = ?"
            params.append(self.filtro_pagamento.currentText())

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        vendas = cursor.fetchall()

        self.tabela.setRowCount(0)
        for linha, venda in enumerate(vendas):
            self.tabela.insertRow(linha)
            for coluna, valor in enumerate(venda):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(str(valor)))

        conn.close()

    def excluir_venda(self):
        if self.tipo != "admin":
            QMessageBox.warning(self, "Acesso Negado", "Somente administradores podem excluir vendas.")
            return

        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma venda para excluir.")
            return

        venda_id = self.tabela.item(linha_selecionada, 0).text()

        resposta = QMessageBox.question(
            self, "Confirmação", f"Tem certeza que deseja excluir a venda ID {venda_id}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if resposta == QMessageBox.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Exclusão", "Venda excluída com sucesso!")
            self.carregar_vendas()
