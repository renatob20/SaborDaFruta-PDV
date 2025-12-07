# utils/data_sync.py
"""
Solução temporária de sincronização entre janelas
USO: Adicionar em todas as telas que precisam atualizar dados
"""

import sqlite3
import hashlib
from typing import Optional

class DataWatcher:
    """Monitora mudanças no banco de dados"""
    
    def __init__(self, db_path="database/pdv.db"):
        self.db_path = db_path
        self._last_hash = {}
    
    def _get_table_hash(self, table: str) -> str:
        """Calcula hash dos dados da tabela"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Busca última modificação (via timestamp ou count)
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # Se tabela tem coluna updated_at, usa ela
        try:
            cursor.execute(f"SELECT MAX(updated_at) FROM {table}")
            last_update = cursor.fetchone()[0] or ""
        except:
            last_update = ""
        
        conn.close()
        
        # Hash simples: count + última atualização
        data = f"{table}:{count}:{last_update}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def has_changed(self, table: str) -> bool:
        """Verifica se a tabela mudou desde última verificação"""
        current_hash = self._get_table_hash(table)
        last_hash = self._last_hash.get(table)
        
        if last_hash != current_hash:
            self._last_hash[table] = current_hash
            return True
        
        return False


# ==========================================
# EXEMPLO DE USO EM vendas_ui.py
# ==========================================

"""
from utils.data_sync import DataWatcher

class VendasUI(ttk.Window):
    def __init__(self, ...):
        super().__init__(themename="superhero")
        self.data_watcher = DataWatcher()
        
        self._build_ui()
        self._carregar_produtos()
        
        # Inicia monitoramento
        self._iniciar_monitoramento()
    
    def _iniciar_monitoramento(self):
        '''Verifica mudanças a cada 5 segundos'''
        if self.data_watcher.has_changed('produtos'):
            print("⚡ Produtos atualizados! Recarregando...")
            self._carregar_produtos()
        
        # Agenda próxima verificação
        self.after(5000, self._iniciar_monitoramento)
    
    def _carregar_produtos(self):
        # ... seu código atual ...
        pass
"""


# ==========================================
# VERSÃO ALTERNATIVA: Arquivo de flag
# ==========================================

import os
from datetime import datetime

class SimpleFlagSync:
    """
    Versão mais simples: usa arquivo de flag
    Útil se não quiser calcular hash
    """
    
    FLAG_DIR = "temp_flags"
    
    def __init__(self):
        os.makedirs(self.FLAG_DIR, exist_ok=True)
    
    def notify_change(self, table: str):
        """Chamado após salvar/atualizar dados"""
        flag_file = os.path.join(self.FLAG_DIR, f"{table}.flag")
        with open(flag_file, 'w') as f:
            f.write(datetime.now().isoformat())
    
    def check_change(self, table: str) -> bool:
        """Verifica se houve mudança"""
        flag_file = os.path.join(self.FLAG_DIR, f"{table}.flag")
        cache_file = os.path.join(self.FLAG_DIR, f"{table}.cache")
        
        if not os.path.exists(flag_file):
            return False
        
        # Lê timestamp da flag
        with open(flag_file, 'r') as f:
            flag_time = f.read().strip()
        
        # Compara com cache local
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache_time = f.read().strip()
            
            if flag_time != cache_time:
                # Atualiza cache
                with open(cache_file, 'w') as f:
                    f.write(flag_time)
                return True
        else:
            # Primeiro acesso, cria cache
            with open(cache_file, 'w') as f:
                f.write(flag_time)
            return True
        
        return False


# ==========================================
# EXEMPLO DE USO COM FLAG
# ==========================================

"""
# Em produtos_ui.py (ao salvar)
from utils.data_sync import SimpleFlagSync

class ProdutosUI(ttk.Window):
    def __init__(self, ...):
        super().__init__(themename="superhero")
        self.sync = SimpleFlagSync()
        # ...
    
    def salvar_produto(self):
        # ... salva no banco ...
        
        # Notifica mudança
        self.sync.notify_change('produtos')
        
        messagebox.showinfo("Sucesso", "Produto salvo!")


# Em vendas_ui.py (ao monitorar)
from utils.data_sync import SimpleFlagSync

class VendasUI(ttk.Window):
    def __init__(self, ...):
        super().__init__(themename="superhero")
        self.sync = SimpleFlagSync()
        
        self._build_ui()
        self._iniciar_monitoramento()
    
    def _iniciar_monitoramento(self):
        if self.sync.check_change('produtos'):
            print("📦 Produtos atualizados!")
            self._carregar_produtos()
        
        self.after(3000, self._iniciar_monitoramento)
"""