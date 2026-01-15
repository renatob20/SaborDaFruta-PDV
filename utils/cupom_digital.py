# utils/cupom_digital.py
"""
Sistema de Cupom Digital com QR Code e Servidor Web
Gera HTML do cupom e serve via HTTP para acesso móvel
"""

import os
import qrcode
from datetime import datetime
from decimal import Decimal
import webbrowser
import base64
from io import BytesIO
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json


class CupomHTTPHandler(SimpleHTTPRequestHandler):
    """Handler personalizado para servir cupons"""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)
    
    def log_message(self, format, *args):
        """Suprime logs do servidor"""
        pass


class ServidorCupons:
    """Servidor HTTP para disponibilizar cupons na rede local"""
    
    def __init__(self, porta=8080, cupons_dir="cupons_digitais"):
        self.porta = porta
        self.cupons_dir = cupons_dir
        self.servidor = None
        self.thread = None
        self.url_base = None
        
        # Garante que a pasta existe
        if not os.path.exists(cupons_dir):
            os.makedirs(cupons_dir)
    
    def obter_ip_local(self):
        """Obtém IP local da máquina na rede"""
        try:
            # Cria socket temporário para descobrir IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def iniciar(self):
        """Inicia servidor HTTP em background"""
        if self.servidor:
            print("⚠️ Servidor já está rodando")
            return self.url_base
        
        try:
            # Salva diretório atual
            original_dir = os.getcwd()
            
            # Garante que diretório existe
            cupons_path = os.path.abspath(self.cupons_dir)
            if not os.path.exists(cupons_path):
                os.makedirs(cupons_path)
            
            # Cria handler com diretório absoluto
            handler = lambda *args, **kwargs: CupomHTTPHandler(
                *args, 
                directory=cupons_path,
                **kwargs
            )
            
            # Cria servidor
            self.servidor = HTTPServer(('0.0.0.0', self.porta), handler)
            
            # Obtém IP local
            ip_local = self.obter_ip_local()
            self.url_base = f"http://{ip_local}:{self.porta}"
            
            # Inicia servidor em thread separada
            self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
            self.thread.start()
            
            # Volta para diretório original
            os.chdir(original_dir)
            
            print(f"✅ Servidor iniciado em: {self.url_base}")
            print(f"📁 Servindo arquivos de: {cupons_path}")
            print(f"📱 Cupons acessíveis na rede local!")
            
            return self.url_base
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return None
    
    def parar(self):
        """Para o servidor"""
        if self.servidor:
            self.servidor.shutdown()
            self.servidor = None
            print("⏹️ Servidor parado")


# Instância global do servidor
_servidor_global = None


def obter_servidor(porta=8080):
    """Obtém ou cria instância única do servidor"""
    global _servidor_global
    
    if _servidor_global is None:
        _servidor_global = ServidorCupons(porta=porta)
        _servidor_global.iniciar()
    
    return _servidor_global


class CupomDigital:
    """Gerador de cupom digital com QR Code e servidor web"""
    
    def __init__(self, output_dir="cupons_digitais", usar_servidor=True, porta=8080):
        """
        Args:
            output_dir: Pasta onde os cupons HTML serão salvos
            usar_servidor: Se True, inicia servidor HTTP local
            porta: Porta do servidor HTTP
        """
        self.output_dir = output_dir
        self.usar_servidor = usar_servidor
        self.porta = porta
        
        # Cria pasta se não existir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Inicia servidor se solicitado
        self.servidor = None
        if usar_servidor:
            self.servidor = obter_servidor(porta)
    
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
        Gera HTML do cupom estilo térmico com novo layout
        
        Args:
            venda_data: dict com dados da venda
        
        Returns:
            str: HTML do cupom
        """
        empresa = venda_data.get('empresa', {})
        
        # Formata data/hora
        try:
            dt = datetime.fromisoformat(venda_data['data_venda'])
            data_str = dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            data_str = venda_data['data_venda']
        
        # Monta HTML estilo cupom térmico com novo layout
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
            padding: 25px 15px;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: slideIn 0.5s ease-out;
            line-height: 1.6;
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
        
        .separador-bold {{
            border-top: 2px solid #333;
            margin: 12px 0;
        }}
        
        .separador-tracos {{
            border-top: 1px dashed #333;
            margin: 12px 0;
        }}
        
        .centro {{
            text-align: center;
        }}
        
        .empresa-nome {{
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
            text-transform: uppercase;
        }}
        
        .empresa-info {{
            font-size: 11px;
            color: #333;
            line-height: 1.8;
        }}
        
        .cupom-tipo {{
            font-size: 14px;
            font-weight: bold;
            margin: 15px 0;
        }}
        
        .venda-info {{
            font-size: 11px;
            color: #333;
            line-height: 1.8;
            margin: 10px 0;
        }}
        
        .itens-cabecalho {{
            font-size: 10px;
            font-weight: bold;
            margin: 10px 0 5px 0;
            display: flex;
            justify-content: space-between;
            padding: 0 5px;
        }}
        
        .itens {{
            margin: 10px 0;
        }}
        
        .item {{
            font-size: 10px;
            margin: 8px 0;
            padding: 0 5px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        
        .item-desc {{
            flex: 1;
            word-break: break-word;
        }}
        
        .item-valor {{
            text-align: right;
            min-width: 70px;
        }}
        
        .total-secao {{
            margin: 12px 0;
            padding: 8px 0;
        }}
        
        .total-linha {{
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            font-size: 14px;
            margin: 8px 0;
        }}
        
        .pagamento-secao {{
            font-size: 11px;
            margin: 10px 0;
            padding: 8px 0;
            line-height: 1.8;
        }}
        
        .pagamento-linha {{
            display: flex;
            justify-content: space-between;
        }}
        
        .rodape {{
            text-align: center;
            font-size: 11px;
            color: #333;
            margin-top: 15px;
            line-height: 1.8;
        }}
        
        .rodape-msg {{
            font-weight: bold;
            margin: 8px 0;
        }}
        
        .btn-imprimir {{
            display: block;
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
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
        <!-- Cabeçalho -->
        <div class="separador-bold"></div>
        <div class="centro">
            <div class="empresa-nome">{empresa.get('nome', 'EMPRESA')}</div>
        </div>
        <div class="separador-bold"></div>
        
        <!-- Dados Empresa -->
        <div class="empresa-info centro">
"""
        
        if empresa.get('cnpj'):
            html += f"            CNPJ: {empresa['cnpj']}<br>\n"
        if empresa.get('endereco'):
            html += f"            {empresa['endereco']}<br>\n"
        if empresa.get('telefone'):
            html += f"            Tel: {empresa['telefone']}<br>\n"
        
        html += f"""
        </div>
        
        <!-- Separador -->
        <div class="separador-tracos"></div>
        
        <!-- Tipo de Comprovante -->
        <div class="cupom-tipo centro">
            NÃO É CUPOM FISCAL
        </div>
        
        <!-- Separador -->
        <div class="separador-tracos"></div>
        
        <!-- Info Venda -->
        <div class="venda-info">
            <strong>Data:</strong> {data_str} &nbsp;&nbsp;&nbsp; <strong>Venda #:</strong> {venda_data['id']:06d}<br>
            <strong>Operador:</strong> {venda_data.get('operador', 'Sistema')}
        </div>
        
        <!-- Separador -->
        <div class="separador-tracos"></div>
        
        <!-- Cabeçalho Itens -->
        <div class="itens-cabecalho">
            <span>ITEM  DESCRIÇÃO</span>
            <span>QTD         VALOR</span>
        </div>
        
        <!-- Separador -->
        <div class="separador-tracos"></div>
        
        <!-- Itens -->
        <div class="itens">
"""
        
        # Itens da venda
        for idx, item in enumerate(venda_data['items'], 1):
            tipo = item.get('tipo', '')
            sabor = item.get('sabor', '')
            
            if sabor:
                descricao = f"{tipo} {sabor}"
            else:
                descricao = item.get('produto_nome', tipo)
            
            # Limita descrição a 16 caracteres
            descricao = descricao[:16]
            
            # Quantidade ou peso
            if item.get('peso_kg') is not None:
                qtd_str = f"{item['peso_kg']:.3f}kg"
            else:
                qtd_str = f"{item['quantidade']}un"
            
            subtotal = self._format_brl(item.get('subtotal', 0))
            
            html += f"""            <div class="item">
                <div class="item-desc">{idx:02d}. {descricao}</div>
                <div class="item-valor">{qtd_str:>8s}  R${subtotal:>7s}</div>
            </div>
"""
        
        html += """
        </div>
        
        <!-- Separador Final Itens -->
        <div class="separador-bold"></div>
        
        <!-- Total -->
        <div class="total-secao">
"""
        
        total = self._format_brl(venda_data.get('total', 0))
        html += f"""
            <div class="total-linha">
                <span>TOTAL</span>
                <span>R$ {total}</span>
            </div>
        </div>
        
        <!-- Separador -->
        <div class="separador-bold"></div>
        
        <!-- Pagamento -->
        <div class="pagamento-secao">
            <div class="pagamento-linha">
                <strong>Forma de Pagamento:</strong>
                <span>{venda_data.get('forma_pagamento', 'N/A')}</span>
            </div>
"""
        
        # Valor recebido e troco (apenas para dinheiro)
        if venda_data.get('forma_pagamento', '').lower() == 'dinheiro':
            valor_recebido = self._format_brl(venda_data.get('valor_recebido', 0))
            troco = self._format_brl(venda_data.get('troco', 0))
            
            html += f"""
            <div class="pagamento-linha">
                <span>Valor Recebido</span>
                <span>R$ {valor_recebido}</span>
            </div>
            <div class="pagamento-linha">
                <span>Troco</span>
                <span>R$ {troco}</span>
            </div>
"""
        
        html += """
        </div>
        
        <!-- Separador -->
        <div class="separador-tracos"></div>
        
        <!-- Rodapé -->
        <div class="rodape">
"""
        
        mensagem = empresa.get('mensagem', 'Obrigado pela preferência!')
        html += f"""
            <div class="rodape-msg">{mensagem}</div>
"""
        
        if empresa.get('site'):
            html += f"""
            <div>{empresa['site']}</div>
"""
        
        html += f"""
            <div style="margin-top: 10px; font-size: 10px;">
                Gerado em {datetime.now().strftime('%d/%m %H:%M')}
            </div>
        </div>
        
        <div class="separador-bold"></div>
        
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
        Gera QR Code que aponta para o cupom HTML via rede local
        
        Args:
            venda_id: ID da venda
            venda_data: dados da venda
        
        Returns:
            tuple: (caminho_html, caminho_qrcode, url_cupom)
        """
        # Gera HTML do cupom
        html_content = self.gerar_html_cupom(venda_data)
        
        # Garante que o diretório existe
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Salva HTML com caminho absoluto
        html_filename = f"cupom_{venda_id:06d}.html"
        html_path = os.path.join(os.path.abspath(self.output_dir), html_filename)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Define URL do cupom
        if self.usar_servidor and self.servidor:
            # URL na rede local (acessível por celular)
            cupom_url = f"{self.servidor.url_base}/{html_filename}"
        else:
            # URL local (só funciona no computador)
            cupom_url = f"file:///{html_path.replace(os.sep, '/')}"
        
        # Gera QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(cupom_url)
        qr.make(fit=True)
        
        # Cria imagem do QR Code
        qr_img = qr.make_image(fill_color="#667eea", back_color="white")
        
        # Salva QR Code com caminho absoluto
        qr_filename = f"qrcode_{venda_id:06d}.png"
        qr_path = os.path.join(os.path.abspath(self.output_dir), qr_filename)
        qr_img.save(qr_path)
        
        return html_path, qr_path, cupom_url
    
    def gerar_pagina_qrcode(self, venda_id, venda_data):
        """
        Gera página HTML com QR Code para o cliente escanear
        
        Returns:
            tuple: (caminho_pagina_qr, url_cupom)
        """
        html_path, qr_path, cupom_url = self.gerar_qrcode(venda_id, venda_data)
        
        # Converte QR Code para base64
        with open(qr_path, 'rb') as f:
            qr_base64 = base64.b64encode(f.read()).decode()
        
        # IP e porta do servidor
        if self.servidor:
            ip_info = f"""
            <div class="network-info">
                <p><strong>📶 Rede:</strong> {self.servidor.url_base}</p>
                <p style="font-size: 11px; color: #999;">
                    Cliente e PDV devem estar na mesma rede Wi-Fi
                </p>
            </div>
"""
        else:
            ip_info = ""
        
        # Gera página com QR Code (código igual ao anterior, sem alterações CSS)
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
        
        .network-info {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }}
        
        .network-info p {{
            margin: 5px 0;
            color: #856404;
            font-size: 13px;
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
        
        {ip_info}
        
        <div class="qrcode">
            <img src="data:image/png;base64,{qr_base64}" alt="QR Code do Cupom">
        </div>
        
        <div class="instrucoes">
            <h3>📲 Como usar:</h3>
            <ol>
                <li>Conecte seu celular na mesma rede Wi-Fi</li>
                <li>Abra a câmera do seu celular</li>
                <li>Aponte para o QR Code acima</li>
                <li>Toque na notificação que aparecer</li>
                <li>Visualize seu cupom completo!</li>
            </ol>
        </div>
        
        <div class="botoes">
            <a href="{cupom_url}" target="_blank" class="btn btn-primary">
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
        
        # Salva página do QR Code com caminho absoluto
        qr_page_filename = f"qrcode_page_{venda_id:06d}.html"
        qr_page_path = os.path.join(os.path.abspath(self.output_dir), qr_page_filename)
        
        with open(qr_page_path, 'w', encoding='utf-8') as f:
            f.write(qr_page)
        
        return qr_page_path, cupom_url


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
            'nome': 
            'AÇAITERIA O SABOR DA FRUTA',
            'cnpj': '13.215.869/0001-03',
            'endereco': 'Estrada do pau ferro, pitomba',
            'telefone': '(75) 98187-7711',
            'mensagem': 'Obrigado pela preferencia!',
            'Instagran': '@acaiteriasabordafruta_'
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
            }
        ]
    }
    
    print("📱 Gerando cupom digital COM SERVIDOR...")
    
    cupom = CupomDigital(usar_servidor=True, porta=8080)
    qr_page_path, cupom_url = cupom.gerar_pagina_qrcode(123, dados_teste)
    
    print(f"✅ QR Code gerado: {qr_page_path}")
    print(f"🌐 URL do cupom: {cupom_url}")
    print(f"📱 Escaneie o QR Code no celular!")
    print(f"🔧 Servidor rodando em: {cupom.servidor.url_base}")
    
    import webbrowser
    webbrowser.open(f"file:///{os.path.abspath(qr_page_path)}")
    
    print("\n✅ Teste concluído!")
    print("⚠️ Mantenha este script rodando enquanto testa no celular")
    input("Pressione ENTER para encerrar o servidor...")


if __name__ == '__main__':
    testar_cupom_digital()