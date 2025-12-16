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
            nome_completo TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            celular TEXT,
            display_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            senha BLOB NOT NULL,  -- ALTERADO PARA BLOB PARA ARMAZENAR HASHES
            role TEXT DEFAULT 'operador',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    
        );
    """)
    # 🔧 MIGRATIONS AUTOMÁTICAS
    cur.execute("PRAGMA table_info(usuarios)")
    cols = [c[1] for c in cur.fetchall()]

    def add_col(col, sql):
        if col not in cols:
            print(f"🔄 Adicionando coluna '{col}' em usuarios...")
            cur.execute(sql)
            print(f"✅ Coluna '{col}' adicionada!")

    add_col("nome_completo", "ALTER TABLE usuarios ADD COLUMN nome_completo TEXT")
    add_col("cpf", "ALTER TABLE usuarios ADD COLUMN cpf TEXT")
    add_col("celular", "ALTER TABLE usuarios ADD COLUMN celular TEXT")
    add_col("created_at", "ALTER TABLE usuarios ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")




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
    # Verifica se precisa recriar a tabela (se tiver coluna 'quantidade' errada)
    cur.execute("PRAGMA table_info(vendas)")
    vendas_cols = [c[1] for c in cur.fetchall()]
    
    if "quantidade" in vendas_cols:
        print("⚠️ Estrutura antiga detectada! Recriando tabela vendas...")
        
        # Salvar dados antigos
        try:
            cur.execute("""
                SELECT id, data_venda, operador, forma_pagamento, 
                       COALESCE(valor_recebido, 0.0), COALESCE(troco, 0.0), 
                       COALESCE(total, 0.0), COALESCE(tipo_produto, 'Diversos')
                FROM vendas
            """)
            old_data = cur.fetchall()
        except:
            old_data = []
        
        # Renomear tabela antiga
        cur.execute("DROP TABLE IF EXISTS vendas_old")
        cur.execute("ALTER TABLE vendas RENAME TO vendas_old")
        
        # Criar tabela nova com estrutura correta
        cur.execute("""
            CREATE TABLE vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_produto TEXT,
                data_venda TEXT NOT NULL,
                operador TEXT,
                forma_pagamento TEXT,
                valor_recebido REAL DEFAULT 0.0,
                troco REAL DEFAULT 0.0,
                total REAL DEFAULT 0.0
            );
        """)
        
        # Restaurar dados
        for row in old_data:
            cur.execute("""
                INSERT INTO vendas (id, data_venda, operador, forma_pagamento,
                                  valor_recebido, troco, total, tipo_produto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
        
        # Remover tabela antiga
        cur.execute("DROP TABLE vendas_old")
        print("✅ Tabela vendas recriada com sucesso!")
    
    else:
        # Criar tabela se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_produto TEXT,
                data_venda TEXT NOT NULL,
                operador TEXT,
                forma_pagamento TEXT,
                valor_recebido REAL DEFAULT 0.0,
                troco REAL DEFAULT 0.0,
                total REAL DEFAULT 0.0
            );
        """)
        
        # Adicionar colunas faltantes se necessário
        cur.execute("PRAGMA table_info(vendas)")
        cols = [c[1] for c in cur.fetchall()]
        
        if "total" not in cols:
            print("🔄 Adicionando coluna 'total' na tabela vendas...")
            cur.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0.0")
            print("✅ Coluna 'total' adicionada!")
        
        if "tipo_produto" not in cols:
            print("🔄 Adicionando coluna 'tipo_produto' na tabela vendas...")
            cur.execute("ALTER TABLE vendas ADD COLUMN tipo_produto TEXT")
            print("✅ Coluna 'tipo_produto' adicionada!")
        
        if "valor_recebido" not in cols:
            print("🔄 Adicionando coluna 'valor_recebido' na tabela vendas...")
            cur.execute("ALTER TABLE vendas ADD COLUMN valor_recebido REAL DEFAULT 0.0")
            print("✅ Coluna 'valor_recebido' adicionada!")
        
        if "troco" not in cols:
            print("🔄 Adicionando coluna 'troco' na tabela vendas...")
            cur.execute("ALTER TABLE vendas ADD COLUMN troco REAL DEFAULT 0.0")
            print("✅ Coluna 'troco' adicionada!")

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
            preco_unitario REAL,
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


def criar_usuario_admin_padrao():
    """
    Cria um usuário admin padrão se não existir nenhum usuário.
    """
    import bcrypt
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Verifica se já existe algum usuário
    cur.execute("SELECT COUNT(*) FROM usuarios")
    count = cur.fetchone()[0]
    
    if count == 0:
        print("👤 Criando usuário admin padrão...")
        
        # Hash da senha "1234"
        senha_hash = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt())
        
        cur.execute("""
            INSERT INTO usuarios (nome_completo, cpf, celular,
                display_name, username, senha, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Administrador do Sistema",
            "00000000000",
            "00000000000",
            "Administrador",
            "admin",
            "senha_hash",
            "admin"))
        
        conn.commit()
        print("✅ Usuário admin criado!")
        print("   Username: admin")
        print("   Senha: 1234")
    
    conn.close()


# Executa a validação automaticamente ao importar o módulo



# Executa a validação automaticamente ao importar o módulo
ensure_schema()
criar_usuario_admin_padrao()