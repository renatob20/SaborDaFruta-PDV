# models/produto_model.py
import os
import sys

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db import get_connection

def criar_tabela_produtos():
    """
    Não precisa fazer nada aqui, pois db.py já cria a tabela.
    Mantemos a função para compatibilidade.
    """
    pass

def inserir_produto(tipo, sabor, preco, estoque=0):
    """Insere novo produto com a coluna 'nome' preenchida"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Monta o nome automaticamente: Tipo + Sabor
    if sabor and sabor.strip():
        nome = f"{tipo} - {sabor}"
    else:
        nome = tipo
    
    cursor.execute("""
        INSERT INTO produtos (nome, tipo, sabor, preco, estoque)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, tipo, sabor, float(preco), int(estoque)))
    
    conn.commit()
    conn.close()

def listar_produtos():
    """Lista todos os produtos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tipo, sabor, preco, estoque 
        FROM produtos 
        ORDER BY tipo ASC
    """)
    produtos = cursor.fetchall()
    conn.close()
    return produtos

def atualizar_produto(id_produto, tipo, sabor, preco, estoque=0):
    """Atualiza produto existente com a coluna 'nome' preenchida"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Monta o nome automaticamente: Tipo + Sabor
    if sabor and sabor.strip():
        nome = f"{tipo} - {sabor}"
    else:
        nome = tipo
    
    cursor.execute("""
        UPDATE produtos
        SET nome=?, tipo=?, sabor=?, preco=?, estoque=?
        WHERE id=?
    """, (nome, tipo, sabor, float(preco), int(estoque), id_produto))
    
    conn.commit()
    conn.close()

def excluir_produto(id_produto):
    """Exclui produto por ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id=?", (id_produto,))
    conn.commit()
    conn.close()