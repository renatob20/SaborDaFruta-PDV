# database/fix_password_column.py
"""
Script de correção rápida: Renomeia coluna 'senha' para 'password'
Execute uma vez para corrigir o banco de dados
"""

import os
import sys
import sqlite3

# Adiciona o diretório raiz ao path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db import get_connection, DB_PATH


def fix_password_column():
    """Renomeia coluna 'senha' para 'password' na tabela usuarios"""
    
    print("=" * 70)
    print("🔧 CORREÇÃO: Renomeando coluna 'senha' → 'password'")
    print("=" * 70)
    print()
    print(f"📂 Banco de dados: {DB_PATH}")
    print()
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verifica estrutura atual
        cur.execute("PRAGMA table_info(usuarios)")
        colunas = cur.fetchall()
        
        print("📋 Colunas atuais:")
        for col in colunas:
            print(f"   - {col[1]} ({col[2]})")
        print()
        
        # Verifica se já tem 'password'
        nomes_colunas = [col[1] for col in colunas]
        
        if 'password' in nomes_colunas:
            print("✅ Coluna 'password' já existe!")
            print("   Nenhuma alteração necessária.")
            conn.close()
            return True
        
        if 'senha' not in nomes_colunas:
            print("❌ ERRO: Coluna 'senha' não encontrada!")
            print("   A tabela tem uma estrutura inesperada.")
            conn.close()
            return False
        
        print("🔄 Iniciando correção...")
        print()
        
        # 1. Criar nova tabela com 'password'
        print("1️⃣ Criando nova tabela...")
        cur.execute("""
            CREATE TABLE usuarios_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_completo TEXT NOT NULL,
                cpf TEXT NOT NULL UNIQUE,
                celular TEXT,
                display_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password BLOB NOT NULL,
                role TEXT DEFAULT 'operador',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✓ Nova tabela criada")
        
        # 2. Copiar dados
        print("2️⃣ Copiando dados...")
        cur.execute("""
            INSERT INTO usuarios_new 
            (id, nome_completo, cpf, celular, display_name, username, password, role, created_at)
            SELECT id, nome_completo, cpf, celular, display_name, username, senha, role, created_at
            FROM usuarios
        """)
        
        # Verifica quantos foram copiados
        cur.execute("SELECT COUNT(*) FROM usuarios_new")
        total = cur.fetchone()[0]
        print(f"   ✓ {total} usuário(s) copiado(s)")
        
        # 3. Remover tabela antiga
        print("3️⃣ Removendo tabela antiga...")
        cur.execute("DROP TABLE usuarios")
        print("   ✓ Tabela antiga removida")
        
        # 4. Renomear nova tabela
        print("4️⃣ Renomeando nova tabela...")
        cur.execute("ALTER TABLE usuarios_new RENAME TO usuarios")
        print("   ✓ Tabela renomeada")
        
        # Commit
        conn.commit()
        print()
        print("💾 Alterações salvas no banco de dados")
        
        # Verificação final
        print()
        print("🔍 Verificando resultado...")
        cur.execute("PRAGMA table_info(usuarios)")
        colunas_novas = cur.fetchall()
        
        print("📋 Colunas após correção:")
        for col in colunas_novas:
            destaque = " ✅" if col[1] == 'password' else ""
            print(f"   - {col[1]} ({col[2]}){destaque}")
        
        conn.close()
        
        print()
        print("=" * 70)
        print("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)
        print()
        print("Agora você pode cadastrar usuários normalmente.")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERRO DURANTE A CORREÇÃO")
        print("=" * 70)
        print()
        print(f"Erro: {e}")
        print()
        
        import traceback
        traceback.print_exc()
        
        print()
        print("⚠️ O banco pode estar em estado inconsistente.")
        print("   Recomendação: Restaure do backup se disponível.")
        print()
        
        return False


if __name__ == "__main__":
    print()
    input("Pressione ENTER para iniciar a correção...")
    print()
    
    try:
        if fix_password_column():
            print()
            input("Pressione ENTER para sair...")
        else:
            print()
            input("Pressione ENTER para sair...")
    except KeyboardInterrupt:
        print()
        print()
        print("❌ Operação cancelada pelo usuário.")
        print()
    except Exception as e:
        print()
        print(f"❌ Erro inesperado: {e}")
        print()