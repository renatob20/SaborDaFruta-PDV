# utils/cupom_digital.py
"""
Sistema de Cupom Digital com QR Code
Gera HTML do cupom e QR Code para visualização sem papel
"""

import os
import qrcode
from datetime import datetime
from decimal import Decimal
import webbrowser
import base64
from io import BytesIO


class CupomDigital:
    """Gerador de cupom digital com QR Code"""
    
    def __init__(self, output_dir="cupons_digitais"):
        """
        Args:
            output_dir: Pasta onde os cupons HTML serão salvos
        """
        self.output_dir = output_dir
        
        # Cria pasta se não existir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _format_brl(self, value):
        """Formata valor para BRL"""
        try:
            v = Decimal(str(value))
            s = f"{v:,.2f}"
            s = s.replace(",", "X").replace(".", ",").replace("X", ".")
            return s
        except:
            return "0,00"
    
    def gerar_html_cupom(self, venda_data):
        """
        Gera HTML do cupom estilo térmico
        
        Args:
            venda_data: dict com dados da venda (mesmo formato da impressora)
        
        Returns:
            str: HTML do cupom
        """
        empresa = venda_data.get('empresa', {})
        
        # Formata data/hora
        try:
            dt = datetime.fromisoformat(venda_data['data_venda'])
            data_str = dt.strftime('%d/%m/%Y às %H:%M:%S')
        except:
            data_str = venda_data['data_venda']
        
        # Monta HTML estilo cupom térmico
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cupom #{venda_data['id']:06d}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .cupom {{
            background: white;
            width: 100%;
            max-width: 400px;
            padding: 30px 20px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: slideIn 0.5s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .header {{
            text-align: center;
            border-bottom: 2px dashed #333;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        
        .logo {{
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .info {{
            font-size: 12px;
            color: #666;
            line-height: 1.6;
        }}
        
        .titulo {{
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            margin: 20px 0;
            color: #333;
        }}
        
        .venda-info {{
            font-size: 13px;
            margin: 15px 0;
            line-height: 1.8;
            color: #444;
        }}
        
        .linha {{
            border-top: 1px dashed #ccc;
            margin: 15px 0;
        }}
        
        .linha-dupla {{
            border-top: 2px solid #333;
            margin: 20px 0;
        }}
        
        .itens {{
            margin: 20px 0;
        }}
        
        .item {{
            margin: 15px 0;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .item-header {{
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        
        .item-detalhes {{
            font-size: 12px;
            color: #666;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 5px;
        }}
        
        .totais {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid #333;
        }}
        
        .total-linha {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            font-size: 14px;
        }}
        
        .total-principal {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            padding: 15px;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 10px;
            margin: 15px 0;
        }}
        
        .pagamento {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
        }}
        
        .pagamento-linha {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 13px;
        }}
        
        .rodape {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px dashed #333;
            font-size: 12px;
            color: #666;
        }}
        
        .rodape-mensagem {{
            font-size: 14px;
            color: #667eea;
            font-weight: bold;
            margin: 15px 0;
        }}
        
        .badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            margin-top: 10px;
        }}
        
        .btn-imprimir {{
            display: block;
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
            transition: transform 0.2s;
        }}
        
        .btn-imprimir:hover {{
            transform: scale(1.02);
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .cupom {{
                box-shadow: none;
                max-width: 100%;
            }}
            .btn-imprimir {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="cupom">
        <div class="header">
            <div class="logo">{empresa.get('nome', 'SABOR DA FRUTA')}</div>
            <div class="info">
"""
        
        if empresa.get('cnpj'):
            html += f"                CNPJ: {empresa['cnpj']}<br>\n"
        if empresa.get('endereco'):
            html += f"                {empresa['endereco']}<br>\n"
        if empresa.get('telefone'):
            html += f"                Tel: {empresa['telefone']}<br>\n"
        
        html += f"""
            </div>
        </div>
        
        <div class="titulo">
            CUPOM NÃO FISCAL
            <span class="badge">DIGITAL</span>
        </div>
        
        <div class="venda-info">
            <strong>Venda:</strong> #{venda_data['id']:06d}<br>
            <strong>Data:</strong> {data_str}<br>
            <strong>Operador:</strong> {venda_data.get('operador', 'Sistema')}
        </div>
        
        <div class="linha-dupla"></div>
        
        <div class="itens">
"""
        
        # Itens da venda
        for idx, item in enumerate(venda_data['items'], 1):
            tipo = item.get('tipo', '')
            sabor = item.get('sabor', '')
            
            if sabor:
                descricao = f"{tipo} - {sabor}"
            else:
                descricao = item.get('produto_nome', tipo)
            
            # Quantidade ou peso
            if item.get('peso_kg') is not None:
                qtd_str = f"{item['peso_kg']:.3f} kg"
            else:
                qtd_str = f"{item['quantidade']} un"
            
            valor_unit = self._format_brl(item.get('valor_unit', 0))
            subtotal = self._format_brl(item.get('subtotal', 0))
            
            html += f"""
            <div class="item">
                <div class="item-header">
                    <span>{idx:02d}. {descricao}</span>
                    <span>R$ {subtotal}</span>
                </div>
                <div class="item-detalhes">
                    <span>{qtd_str} × R$ {valor_unit}</span>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <div class="totais">
"""
        
        # Total
        total = self._format_brl(venda_data.get('total', 0))
        html += f"""
            <div class="total-linha total-principal">
                <span>TOTAL</span>
                <span>R$ {total}</span>
            </div>
"""
        
        # Forma de pagamento
        forma = venda_data.get('forma_pagamento', '')
        html += f"""
            <div class="pagamento">
                <div class="pagamento-linha">
                    <span><strong>Pagamento:</strong></span>
                    <span>{forma}</span>
                </div>
"""
        
        # Valor recebido e troco (apenas para dinheiro)
        if forma.lower() == 'dinheiro':
            valor_recebido = self._format_brl(venda_data.get('valor_recebido', 0))
            troco = self._format_brl(venda_data.get('troco', 0))
            
            html += f"""
                <div class="pagamento-linha">
                    <span>Valor Recebido:</span>
                    <span>R$ {valor_recebido}</span>
                </div>
                <div class="pagamento-linha">
                    <span>Troco:</span>
                    <span>R$ {troco}</span>
                </div>
"""
        
        html += """
            </div>
        </div>
        
        <div class="rodape">
"""
        
        mensagem = empresa.get('mensagem', 'Obrigado pela preferência!')
        html += f"""
            <div class="rodape-mensagem">{mensagem}</div>
"""
        
        if empresa.get('site'):
            html += f"""
            <div>{empresa['site']}</div>
"""
        
        html += f"""
            <div style="margin-top: 15px; font-size: 11px; color: #999;">
                Cupom digital - Sem valor fiscal<br>
                Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
            </div>
        </div>
        
        <button class="btn-imprimir" onclick="window.print()">
            🖨️ IMPRIMIR CUPOM
        </button>
    </div>
</body>
</html>
"""
        
        return html
    
    def gerar_qrcode(self, venda_id, venda_data):
        """
        Gera QR Code que aponta para o cupom HTML
        
        Args:
            venda_id: ID da venda
            venda_data: dados da venda
        
        Returns:
            tuple: (caminho_html, caminho_qrcode)
        """
        # Gera HTML do cupom
        html_content = self.gerar_html_cupom(venda_data)
        
        # Salva HTML
        html_filename = f"cupom_{venda_id:06d}.html"
        html_path = os.path.join(self.output_dir, html_filename)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Converte caminho absoluto para URL
        html_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
        
        # Gera QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(html_url)
        qr.make(fit=True)
        
        # Cria imagem do QR Code
        qr_img = qr.make_image(fill_color="#667eea", back_color="white")
        
        # Salva QR Code
        qr_filename = f"qrcode_{venda_id:06d}.png"
        qr_path = os.path.join(self.output_dir, qr_filename)
        qr_img.save(qr_path)
        
        return html_path, qr_path
    
    def abrir_cupom_digital(self, venda_id, venda_data):
        """
        Gera cupom e abre no navegador
        
        Args:
            venda_id: ID da venda
            venda_data: dados da venda
        
        Returns:
            tuple: (caminho_html, caminho_qrcode)
        """
        html_path, qr_path = self.gerar_qrcode(venda_id, venda_data)
        
        # Abre HTML no navegador padrão
        webbrowser.open(f"file:///{os.path.abspath(html_path)}")
        
        return html_path, qr_path
    
    def gerar_pagina_qrcode(self, venda_id, venda_data):
        """
        Gera página HTML com QR Code para o cliente escanear
        
        Returns:
            str: caminho do arquivo HTML com QR Code
        """
        html_path, qr_path = self.gerar_qrcode(venda_id, venda_data)
        
        # Converte QR Code para base64
        with open(qr_path, 'rb') as f:
            qr_base64 = base64.b64encode(f.read()).decode()
        
        # Gera página com QR Code
        qr_page = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cupom Digital - QR Code</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .container {{
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
            animation: fadeIn 0.6s ease-out;
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: scale(0.9);
            }}
            to {{
                opacity: 1;
                transform: scale(1);
            }}
        }}
        
        h1 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 32px;
        }}
        
        .subtitulo {{
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        
        .qrcode {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            border: 3px solid #667eea;
            display: inline-block;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
        }}
        
        .qrcode img {{
            width: 280px;
            height: 280px;
            display: block;
        }}
        
        .instrucoes {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
            text-align: left;
        }}
        
        .instrucoes h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        
        .instrucoes ol {{
            color: #666;
            line-height: 2;
            padding-left: 20px;
        }}
        
        .venda-info {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        
        .venda-info p {{
            margin: 5px 0;
            color: #333;
            font-size: 14px;
        }}
        
        .botoes {{
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }}
        
        .btn {{
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn:hover {{
            transform: scale(1.05);
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .btn-secondary {{
            background: #f8f9fa;
            color: #333;
            border: 2px solid #ddd;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
            .botoes {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Cupom Digital</h1>
        <p class="subtitulo">Escaneie para visualizar seu cupom</p>
        
        <div class="venda-info">
            <p><strong>Venda:</strong> #{venda_id:06d}</p>
            <p><strong>Total:</strong> R$ {self._format_brl(venda_data.get('total', 0))}</p>
        </div>
        
        <div class="qrcode">
            <img src="data:image/png;base64,{qr_base64}" alt="QR Code do Cupom">
        </div>
        
        <div class="instrucoes">
            <h3>📲 Como usar:</h3>
            <ol>
                <li>Abra a câmera do seu celular</li>
                <li>Aponte para o QR Code acima</li>
                <li>Toque na notificação que aparecer</li>
                <li>Visualize seu cupom completo!</li>
            </ol>
        </div>
        
        <div class="botoes">
            <a href="{html_path}" target="_blank" class="btn btn-primary">
                👁️ VER CUPOM
            </a>
            <button onclick="window.print()" class="btn btn-secondary">
                🖨️ IMPRIMIR QR CODE
            </button>
        </div>
    </div>
</body>
</html>
"""
        
        # Salva página do QR Code
        qr_page_filename = f"qrcode_page_{venda_id:06d}.html"
        qr_page_path = os.path.join(self.output_dir, qr_page_filename)
        
        with open(qr_page_path, 'w', encoding='utf-8') as f:
            f.write(qr_page)
        
        return qr_page_path


# ========== FUNÇÃO DE TESTE ==========
def testar_cupom_digital():
    """Testa geração de cupom digital"""
    from datetime import datetime
    
    dados_teste = {
        'id': 123,
        'data_venda': datetime.now().isoformat(),
        'operador': 'João Silva',
        'forma_pagamento': 'Dinheiro',
        'total': 45.50,
        'valor_recebido': 50.00,
        'troco': 4.50,
        'empresa': {
            'nome': 'SABOR DA FRUTA',
            'cnpj': '12.345.678/0001-90',
            'endereco': 'Rua Exemplo, 123 - Centro',
            'telefone': '(11) 98765-4321',
            'mensagem': 'Volte sempre!',
            'site': 'www.sabordafruta.com.br'
        },
        'items': [
            {
                'tipo': 'Açaí',
                'sabor': 'Tradicional',
                'peso_kg': 0.500,
                'valor_unit': 45.00,
                'subtotal': 22.50
            },
            {
                'tipo': 'Adicional',
                'sabor': 'Granola',
                'quantidade': 1,
                'valor_unit': 3.00,
                'subtotal': 3.00
            },
            {
                'tipo': 'Sorvete',
                'sabor': 'Chocolate',
                'peso_kg': 0.400,
                'valor_unit': 50.00,
                'subtotal': 20.00
            }
        ]
    }
    
    print("📱 Gerando cupom digital...")
    
    cupom = CupomDigital()
    qr_page_path = cupom.gerar_pagina_qrcode(123, dados_teste)
    
    print(f"✅ QR Code gerado: {qr_page_path}")
    print(f"🌐 Abrindo no navegador...")
    
    import webbrowser
    webbrowser.open(f"file:///{os.path.abspath(qr_page_path)}")
    
    print("✅ Teste concluído!")


if __name__ == '__main__':
    testar_cupom_digital()