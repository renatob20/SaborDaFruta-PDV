"""
db.py — Gerenciador único de banco de dados do sistema
------------------------------------------------------

📌 Responsável por:
 - Criar conexão única com o SQLite
 - Garantir tabelas necessárias
 - Executar migrations automáticas (sem perder dados)
"""

import os
import sqlite3

# 🔹 Caminho do arquivo SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), "acaiteria.db")


def get_connection():
    """
    Retorna uma conexão com o banco.
    Sempre use esta função em vez de sqlite3.connect diretamente.
    """
    return sqlite3.connect(DB_PATH)

def ensure_schema():
    """
    Garante que TODAS as tabelas existam.
    Também corrige colunas faltantes automaticamente.
    """

    conn = get_connection()
    cur = conn.cursor()

    # ---------------------- TABELA USUÁRIOS ----------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            role TEXT DEFAULT 'operador'
        );
    """)

    # ---------------------- TABELA PRODUTOS ----------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            tipo TEXT NOT NULL,
            sabor TEXT,
            preco REAL NOT NULL,
            estoque INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 🔧 Migration: Adiciona coluna 'nome' se não existir
    cur.execute("PRAGMA table_info(produtos)")
    cols = [c[1] for c in cur.fetchall()]
    
    if "nome" not in cols:
        print("🔄 Adicionando coluna 'nome' na tabela produtos...")
        cur.execute("ALTER TABLE produtos ADD COLUMN nome TEXT")
        cur.execute("""
            UPDATE produtos 
            SET nome = tipo || CASE 
                WHEN sabor IS NOT NULL AND sabor != '' 
                THEN ' - ' || sabor 
                ELSE '' 
            END
            WHERE nome IS NULL OR nome = ''
        """)
        print("✅ Coluna 'nome' adicionada e preenchida!")

    # ---------------------- TABELA VENDAS ----------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda TEXT NOT NULL,
            operador TEXT,
            forma_pagamento TEXT,
            valor_recebido REAL,
            troco REAL,
            total REAL DEFAULT 0.0
        );
    """)

    # 🔧 Corrige coluna `total` se não existir
    cur.execute("PRAGMA table_info(vendas)")
    cols = [c[1] for c in cur.fetchall()]
    if "total" not in cols:
        print("🔄 Adicionando coluna 'total' na tabela vendas...")
        cur.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0.0")
        print("✅ Coluna 'total' adicionada!")

    # ---------------------- ITENS DA VENDA ----------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS venda_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER,
            produto_nome TEXT,
            tipo TEXT,
            quantidade INTEGER,
            peso_kg REAL,
            valor_unit REAL,
            subtotal REAL,
            FOREIGN KEY(venda_id) REFERENCES vendas(id)
        );
    """)

    # ---------------------- TABELA PONTO ----------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ponto_batidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()


# Executa a validação automaticamente ao importar o módulo
ensure_schema()