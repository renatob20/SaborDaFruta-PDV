"""
db.py – Gerenciador único de banco de dados do sistema
------------------------------------------------------
VERSÃO CORRIGIDA PARA FUNCIONAR EM EXECUTÁVEL PYINSTALLER
INCLUI TRATAMENTO DE ERROS MELHORADO

🔌 Responsável por:
 - Criar conexão única com o SQLite
 - Garantir tabelas necessárias
 - Executar migrations automáticas (sem perder dados)
 - Funcionar tanto em desenvolvimento quanto em executável
"""

import os
import sys
import sqlite3
import traceback

def get_db_path():
    """
    Retorna caminho correto do banco, funciona tanto em dev quanto em executável.
    
    IMPORTANTE: Esta função resolve o problema de "unable to open database file"
    quando o sistema roda como executável PyInstaller.
    """
    try:
        if getattr(sys, 'frozen', False):
            # Executando como executável PyInstaller
            # sys.executable aponta para o .exe
            application_path = os.path.dirname(sys.executable)
            print(f"🔧 Modo: Executável")
        else:
            # Executando em modo desenvolvimento
            application_path = os.path.dirname(os.path.abspath(__file__))
            print(f"🔧 Modo: Desenvolvimento")
        
        print(f"📂 Caminho da aplicação: {application_path}")
        
        # Garante que a pasta database existe
        db_dir = os.path.join(application_path, 'database')
        
        # Tenta criar a pasta, se falhar tenta no diretório do usuário
        try:
            os.makedirs(db_dir, exist_ok=True)
        except (PermissionError, OSError) as e:
            print(f"⚠️ Não foi possível criar em {db_dir}")
            # Fallback: usar pasta do usuário
            user_dir = os.path.expanduser("~")
            db_dir = os.path.join(user_dir, "SaborDaFruta-PDV", "database")
            os.makedirs(db_dir, exist_ok=True)
            print(f"📂 Usando pasta alternativa: {db_dir}")
        
        db_path = os.path.join(db_dir, "acaiteria.db")
        print(f"💾 Banco de dados: {db_path}")
        
        return db_path
    
    except Exception as e:
        print(f"❌ Erro ao determinar caminho do banco: {e}")
        traceback.print_exc()
        # Fallback final: pasta do usuário
        user_dir = os.path.expanduser("~")
        db_dir = os.path.join(user_dir, "SaborDaFruta-PDV", "database")
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "acaiteria.db")

# 🔹 Caminho do arquivo SQLite
DB_PATH = get_db_path()


def get_connection():
    """
    Retorna uma conexão com o banco.
    Sempre use esta função em vez de sqlite3.connect diretamente.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        return conn
    except sqlite3.OperationalError as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        print(f"📂 Caminho tentado: {DB_PATH}")
        traceback.print_exc()
        raise
    except Exception as e:
        print(f"❌ Erro inesperado ao conectar: {e}")
        traceback.print_exc()
        raise


def ensure_schema():
    """
    Garante que TODAS as tabelas existam.
    Também corrige colunas faltantes automaticamente.
    """
    
    try:
        print("🔧 Verificando schema do banco de dados...")

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
                senha BLOB NOT NULL,
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
                try:
                    cur.execute(sql)
                    print(f"✅ Coluna '{col}' adicionada!")
                except Exception as e:
                    print(f"⚠️ Erro ao adicionar coluna '{col}': {e}")

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
            try:
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
            except Exception as e:
                print(f"⚠️ Erro ao adicionar coluna 'nome': {e}")

        # ---------------------- TABELA VENDAS ----------------------
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
        
        # Adicionar colunas faltantes
        cur.execute("PRAGMA table_info(vendas)")
        cols = [c[1] for c in cur.fetchall()]
        
        if "total" not in cols:
            print("🔄 Adicionando coluna 'total' na tabela vendas...")
            try:
                cur.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0.0")
                print("✅ Coluna 'total' adicionada!")
            except Exception as e:
                print(f"⚠️ Erro: {e}")
        
        if "tipo_produto" not in cols:
            print("🔄 Adicionando coluna 'tipo_produto' na tabela vendas...")
            try:
                cur.execute("ALTER TABLE vendas ADD COLUMN tipo_produto TEXT")
                print("✅ Coluna 'tipo_produto' adicionada!")
            except Exception as e:
                print(f"⚠️ Erro: {e}")
        
        if "valor_recebido" not in cols:
            print("🔄 Adicionando coluna 'valor_recebido' na tabela vendas...")
            try:
                cur.execute("ALTER TABLE vendas ADD COLUMN valor_recebido REAL DEFAULT 0.0")
                print("✅ Coluna 'valor_recebido' adicionada!")
            except Exception as e:
                print(f"⚠️ Erro: {e}")
        
        if "troco" not in cols:
            print("🔄 Adicionando coluna 'troco' na tabela vendas...")
            try:
                cur.execute("ALTER TABLE vendas ADD COLUMN troco REAL DEFAULT 0.0")
                print("✅ Coluna 'troco' adicionada!")
            except Exception as e:
                print(f"⚠️ Erro: {e}")

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
        
        print("✅ Schema verificado e atualizado!")
        return True
    
    except Exception as e:
        print(f"❌ Erro ao garantir schema: {e}")
        traceback.print_exc()
        return False


def criar_usuario_admin_padrao():
    """
    Cria um usuário admin padrão se não existir nenhum usuário.
    
    IMPORTANTE: Esta função só deve ser chamada explicitamente,
    não automaticamente ao importar o módulo.
    """
    try:
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
                senha_hash,
                "admin"))
            
            conn.commit()
            print("✅ Usuário admin criado!")
            print("   Username: admin")
            print("   Senha: 1234")
        else:
            print(f"ℹ️ Sistema já possui {count} usuário(s) cadastrado(s)")
        
        conn.close()
        return True
    
    except ImportError as e:
        print(f"❌ Erro ao importar bcrypt: {e}")
        print("   Certifique-se de que bcrypt está instalado")
        traceback.print_exc()
        return False
    
    except Exception as e:
        print(f"❌ Erro ao criar usuário admin: {e}")
        traceback.print_exc()
        return False


# IMPORTANTE: NÃO executar automaticamente ao importar
# As funções devem ser chamadas explicitamente pelo main.py
if __name__ == "__main__":
    # Permite testar o módulo diretamente
    print("🧪 Testando módulo db.py...")
    if ensure_schema():
        criar_usuario_admin_padrao()
        print("✅ Teste concluído!")
    else:
        print("❌ Teste falhou!")