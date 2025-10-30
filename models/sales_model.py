# models/sales_model.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("database", "acaiteria.db")

def create_sales_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda TEXT NOT NULL,
            tipo_produto TEXT NOT NULL,
            sabor TEXT,
            quantidade REAL NOT NULL,
            valor_unit REAL NOT NULL,
            valor_total REAL NOT NULL,
            forma_pagamento TEXT NOT NULL,
            operador TEXT NOT NULL,
            observacoes TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_venda(tipo, sabor, qtd, valor_unit, forma_pagamento, operador, observacoes=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    valor_total = qtd * valor_unit
    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO vendas (data_venda, tipo_produto, sabor, quantidade, valor_unit,
                            valor_total, forma_pagamento, operador, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data_venda, tipo, sabor, qtd, valor_unit, valor_total, forma_pagamento, operador, observacoes))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_sales_table()
    print("sales table ready")
