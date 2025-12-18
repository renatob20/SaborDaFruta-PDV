# config/version.py
"""
Informações de versão do sistema
"""

__version__ = "1.0.0"
__app_name__ = "Sabor da Fruta PDV"
__author__ = "Renato"
__license__ = "Proprietário"
__build_date__ = "2025-01-17"

# Histórico de versões
CHANGELOG = {
    "1.0.0": [
        "✨ Versão inicial",
        "✅ Sistema de vendas completo",
        "✅ Controle de estoque",
        "✅ Gestão de usuários",
        "✅ Cupom digital com QR Code",
        "✅ Impressão térmica",
        "✅ Relatórios básicos"
    ]
}

def get_version_info():
    """Retorna informações da versão atual"""
    return {
        "version": __version__,
        "app_name": __app_name__,
        "author": __author__,
        "build_date": __build_date__
    }
##```

##---

## 🗂️ **PASSO 2: CRIAR PASTA DE ASSETS**

### **2.1 - Estrutura de Assets**

##**O que é:** Pasta com ícones, imagens e recursos visuais

##**Por que é importante:** O executável precisa desses arquivos para aparecer bonito

##**Como criar:**
##```
##assets/
##├── icons/
##│   ├── app.ico          (ícone do programa - 256x256)
##│   ├── vendas.png       (ícone do menu vendas)
##│   ├── produtos.png     (ícone do menu produtos)
##│   └── relatorios.png   (ícone do menu relatórios)
##└── images/
##    ├── logo.png         (logo da empresa)
##    └── splash.png       (tela de carregamento)