import subprocess
import sys
from pathlib import Path

print("🔧 Preparando build...")

# Cria hooks
hooks_dir = Path('hooks')
hooks_dir.mkdir(exist_ok=True)

(hooks_dir / 'hook-bcrypt.py').write_text("""
from PyInstaller.utils.hooks import collect_all, collect_submodules
datas, binaries, hiddenimports = collect_all('bcrypt')
hiddenimports += collect_submodules('bcrypt')
hiddenimports += ['bcrypt._bcrypt', '_cffi_backend']
""")

(hooks_dir / 'hook-ttkbootstrap.py').write_text("""
from PyInstaller.utils.hooks import collect_all
datas, binaries, hiddenimports = collect_all('ttkbootstrap')
""")

print("✅ Hooks criados")
print("🚀 Executando PyInstaller...")

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--noconfirm',
    '--windowed',
    '--onedir',
    '--name=SaborDaFruta-PDV',
    '--additional-hooks-dir=hooks',
    '--icon=assets/icons/app.ico',
    
    # Adicionar TUDO
    '--add-data=assets;assets',
    '--add-data=config;config',
    '--add-data=ui;ui',              # NOVO - Copia pasta ui/
    '--add-data=database;database',  # NOVO - Copia pasta database/
    '--add-data=controllers;controllers',  # NOVO
    '--add-data=models;models',      # NOVO
    '--add-data=services;services',  # NOVO
    '--add-data=utils;utils',        # NOVO
    '--add-data=views;views',        # NOVO
    
    # Collect ALL
    '--collect-all=bcrypt',
    '--collect-all=_cffi_backend',
    '--collect-all=ttkbootstrap',
    
    # Hidden imports
    '--hidden-import=bcrypt',
    '--hidden-import=bcrypt._bcrypt',
    '--hidden-import=_cffi_backend',
    '--hidden-import=ttkbootstrap',
    '--hidden-import=ttkbootstrap.constants',
    '--hidden-import=ttkbootstrap.themes',
    '--hidden-import=qrcode',
    '--hidden-import=PIL',
    '--hidden-import=PIL._imaging',
    '--hidden-import=win32print',
    '--hidden-import=win32api',
    '--hidden-import=win32con',
    '--hidden-import=pywintypes',
    '--hidden-import=sqlite3',
    
    # Hidden imports de todos os módulos do projeto
    '--hidden-import=ui',
    '--hidden-import=ui.login_ui',
    '--hidden-import=ui.dashboard_ui',
    '--hidden-import=database.db',
    '--hidden-import=database.products_db',
    
    'main.py'
]

result = subprocess.run(cmd)

if result.returncode == 0:
    print("\n✅ BUILD CONCLUÍDO!")
    print("📦 Executável em: dist/SaborDaFruta-PDV/SaborDaFruta-PDV.exe")
    
    # Criar estrutura
    from pathlib import Path
    dist_dir = Path('dist/SaborDaFruta-PDV')
    
    # Pasta database
    (dist_dir / 'database').mkdir(exist_ok=True)
    
    # LEIA-ME
    (dist_dir / 'LEIA-ME.txt').write_text("""
================================================================
            SABOR DA FRUTA PDV v1.0.0
================================================================

INSTALAÇÃO:
1. Copie a pasta completa para C:\\Program Files\\SaborDaFruta-PDV
2. Execute: SaborDaFruta-PDV.exe
3. Login: admin / 1234

IMPORTANTE:
- NÃO delete pasta database/
- NÃO delete pasta _internal/

LOGS: C:\\Users\\[Usuario]\\SaborDaFruta-PDV\\error.log
================================================================
""", encoding='utf-8')
    
    print("\n📋 Estrutura criada!")
    
else:
    print("\n❌ BUILD FALHOU!")

input("\nPressione ENTER...")