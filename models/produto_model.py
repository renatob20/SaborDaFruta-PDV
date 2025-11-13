# models/produto_model.py
from database.db_connection import get_connection

def criar_tabela_produtos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        sabor TEXT NOT NULL,
        preco REAL NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def inserir_produto(nome, tipo, sabor, preco):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO produtos (nome, tipo, sabor, preco)
        VALUES (?, ?, ?, ?)
    """, (nome, tipo, sabor, preco))
    conn.commit()
    conn.close()

def listar_produtos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, tipo, sabor, preco FROM produtos ORDER BY nome ASC")
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def atualizar_produto(id_produto, nome, tipo, sabor, preco):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE produtos
        SET nome=?, tipo=?, sabor=?, preco=?
        WHERE id=?
    """, (nome, tipo, sabor, preco, id_produto))
    conn.commit()
    conn.close()

def excluir_produto(id_produto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id=?", (id_produto,))
    conn.commit()
    conn.close()
