# teste_cupom.py
"""
Script para testar geração de cupom PDF sem fazer venda real
Execute: python teste_cupom.py
"""

import os
import sys
from datetime import datetime

# Ajusta path para importar módulos do projeto
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Importa o gerador de PDF
from utils.cupom_pdf import CupomPDF


def gerar_cupom_teste():
    """Gera um cupom de teste com dados fictícios"""
    
    print("=" * 50)
    print("🧪 GERADOR DE CUPOM DE TESTE")
    print("=" * 50)
    print()
    
    # Dados fictícios da empresa
    dados_teste = {
        'id': 16,
        'data_venda': datetime.now().isoformat(),
        'operador': 'Administrador',
        'forma_pagamento': 'Pix',
        'total': 15.00,
        'valor_recebido': 15.00,
        'troco': 0.00,
        'items': [
            {
                'tipo': 'Picolé',
                'sabor': 'Coco',
                'quantidade': 10,
                'peso_kg': None,
                'valor_unit': 1.50,
                'subtotal': 15.00
            }
        ],
        'empresa': {
            'nome': 'AÇAITERIA O SABOR DA FRUTA',
            'cnpj': '13.215.869/0001-03',
            'endereco': 'Estrada do pau ferro, pitomba',
            'telefone': '(75) 98187-7711',
            'mensagem': 'Obrigado pela preferencia!',
            'site': '@acaiteriasabordafruta_'
        }
    }
    
    print("📋 Dados do cupom:")
    print(f"   Venda #: {dados_teste['id']:06d}")
    print(f"   Operador: {dados_teste['operador']}")
    print(f"   Pagamento: {dados_teste['forma_pagamento']}")
    print(f"   Total: R$ {dados_teste['total']:.2f}")
    print(f"   Itens: {len(dados_teste['items'])}")
    print()
    
    # Gera o PDF
    print("🔄 Gerando PDF...")
    gerador = CupomPDF(largura_mm=80)
    
    # Nome do arquivo de saída
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo = f"cupom_teste_{timestamp}.pdf"
    
    try:
        caminho = gerador.gerar_cupom(dados_teste, arquivo)
        print(f"✅ PDF gerado com sucesso!")
        print(f"📂 Local: {os.path.abspath(caminho)}")
        print()
        
        # Pergunta se quer abrir
        resposta = input("Deseja abrir o arquivo? (s/n): ").strip().lower()
        
        if resposta == 's':
            print("🖥️ Abrindo arquivo...")
            if sys.platform == 'win32':
                os.startfile(caminho)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.call(['open', caminho])
            else:  # Linux
                import subprocess
                subprocess.call(['xdg-open', caminho])
        
        print()
        print("✅ Teste concluído!")
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()


def gerar_cupom_personalizado():
    """Permite personalizar os dados do cupom de teste"""
    
    print("=" * 50)
    print("🎨 GERADOR DE CUPOM PERSONALIZADO")
    print("=" * 50)
    print()
    
    # Coleta dados do usuário
    try:
        venda_id = int(input("ID da venda (ex: 123): ") or "123")
        operador = input("Nome do operador (Enter = Administrador): ") or "Administrador"
        
        print("\nFormas de pagamento: Débito, Crédito, Pix, Dinheiro")
        forma_pag = input("Forma de pagamento (Enter = Pix): ") or "Pix"
        
        # Item
        print("\n--- ADICIONAR ITEM ---")
        tipo = input("Tipo do produto (ex: Picolé): ") or "Picolé"
        sabor = input("Sabor (ex: Morango): ") or "Morango"
        
        # Quantidade ou peso
        opcao = input("Vender por (1) Quantidade ou (2) Peso? (Enter = 1): ") or "1"
        
        if opcao == "2":
            peso = float(input("Peso em KG (ex: 0.500): ") or "0.5")
            preco_kg = float(input("Preço por KG (ex: 45.00): ") or "45.00")
            quantidade = None
            preco_unit = preco_kg
            subtotal = peso * preco_kg
        else:
            quantidade = int(input("Quantidade (ex: 10): ") or "10")
            preco_unit = float(input("Preço unitário (ex: 1.50): ") or "1.50")
            peso = None
            subtotal = quantidade * preco_unit
        
        # Pagamento
        total = subtotal
        if forma_pag.lower() == 'dinheiro':
            valor_recebido = float(input(f"\nValor recebido (Total: R$ {total:.2f}): ") or total)
            troco = valor_recebido - total
        else:
            valor_recebido = total
            troco = 0.0
        
        # Monta dados
        dados_personalizado = {
            'id': venda_id,
            'data_venda': datetime.now().isoformat(),
            'operador': operador,
            'forma_pagamento': forma_pag,
            'total': total,
            'valor_recebido': valor_recebido,
            'troco': troco,
            'items': [
                {
                    'tipo': tipo,
                    'sabor': sabor,
                    'quantidade': quantidade,
                    'peso_kg': peso,
                    'valor_unit': preco_unit,
                    'subtotal': subtotal
                }
            ],
            'empresa': {
                'nome': 'AÇAITERIA O SABOR DA FRUTA',
                'cnpj': '13.215.869/0001-03',
                'endereco': 'Estrada do pau ferro, pitomba',
                'telefone': '(75) 98187-7711',
                'mensagem': 'Obrigado pela preferencia!',
                'site': '@acaiteriasabordafruta_'
            }
        }
        
        # Gera PDF
        print("\n🔄 Gerando PDF personalizado...")
        gerador = CupomPDF(largura_mm=80)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo = f"cupom_personalizado_{timestamp}.pdf"
        
        caminho = gerador.gerar_cupom(dados_personalizado, arquivo)
        print(f"✅ PDF gerado: {os.path.abspath(caminho)}")
        
        # Abre automaticamente
        if sys.platform == 'win32':
            os.startfile(caminho)
        
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    print()
    print("╔════════════════════════════════════════════╗")
    print("║   🧪 TESTADOR DE CUPOM PDF                 ║")
    print("╚════════════════════════════════════════════╝")
    print()
    print("Escolha uma opção:")
    print()
    print("  1 - Gerar cupom de teste rápido")
    print("  2 - Gerar cupom personalizado")
    print("  0 - Sair")
    print()
    
    opcao = input("Opção: ").strip()
    print()
    
    if opcao == "1":
        gerar_cupom_teste()
    elif opcao == "2":
        gerar_cupom_personalizado()
    else:
        print("👋 Até logo!")