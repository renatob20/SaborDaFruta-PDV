# models/produto_model.py
import os
import sys

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db import get_connection  # seu arquivo é db.py

def criar_tabela_produtos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        sabor TEXT NOT NULL,
        preco REAL NOT NULL,
        estoque INTEGER DEFAULT 0
    );
    """)
    conn.commit()
    conn.close()

def inserir_produto(tipo, sabor, preco, estoque=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO produtos (tipo, sabor, preco, estoque)
        VALUES (?, ?, ?, ?)
    """, (tipo, sabor, float(preco), int(estoque)))
    conn.commit()
    conn.close()

def listar_produtos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, sabor, preco, estoque FROM produtos ORDER BY tipo ASC")
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def atualizar_produto(id_produto, tipo, sabor, preco, estoque=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE produtos
        SET tipo=?, sabor=?, preco=?, estoque=?
        WHERE id=?
    """, (tipo, sabor, float(preco), int(estoque), id_produto))
    conn.commit()
    conn.close()

def excluir_produto(id_produto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id=?", (id_produto,))
    conn.commit()
    conn.close()
