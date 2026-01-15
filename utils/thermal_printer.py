# utils/thermal_printer.py
"""
Sistema de impressão para impressoras térmicas
Compatível com impressoras ESC/POS (80mm e 58mm)
"""

import os
import platform
from datetime import datetime
from decimal import Decimal

class ThermalPrinter:
    """Gerenciador de impressão térmica ESC/POS"""
    
    # Comandos ESC/POS
    ESC = b'\x1b'
    GS = b'\x1d'
    
    # Inicialização
    INIT = ESC + b'@'
    
    # Alinhamento
    ALIGN_LEFT = ESC + b'a\x00'
    ALIGN_CENTER = ESC + b'a\x01'
    ALIGN_RIGHT = ESC + b'a\x02'
    
    # Tamanho de fonte
    NORMAL = ESC + b'!\x00'
    DOUBLE_HEIGHT = ESC + b'!\x10'
    DOUBLE_WIDTH = ESC + b'!\x20'
    DOUBLE_SIZE = ESC + b'!\x30'
    
    # Estilo
    BOLD_ON = ESC + b'E\x01'
    BOLD_OFF = ESC + b'E\x00'
    UNDERLINE_ON = ESC + b'-\x01'
    UNDERLINE_OFF = ESC + b'-\x00'
    
    # Corte de papel
    CUT = GS + b'V\x41\x00'
    
    # Feed
    LINE_FEED = b'\n'
    
    def __init__(self, printer_name=None, largura=48):
        """
        Inicializa impressora
        
        Args:
            printer_name: Nome da impressora (None = impressora padrão)
            largura: Largura em caracteres (48 para 80mm, 32 para 58mm)
        """
        self.printer_name = printer_name
        self.largura = largura
        self.buffer = bytearray()
    
    def _add(self, data):
        """Adiciona dados ao buffer"""
        if isinstance(data, str):
            self.buffer.extend(data.encode('cp850', errors='replace'))
        else:
            self.buffer.extend(data)
    
    def _linha(self, char='-'):
        """Adiciona linha separadora"""
        self._add(char * self.largura)
        self._add(self.LINE_FEED)
    
    def _centralizar(self, texto):
        """Centraliza texto"""
        espacos = (self.largura - len(texto)) // 2
        return ' ' * espacos + texto
    
    def _direita(self, texto):
        """Alinha texto à direita"""
        espacos = self.largura - len(texto)
        return ' ' * espacos + texto
    
    def _duas_colunas(self, esq, dir):
        """Formata duas colunas (esquerda e direita)"""
        espacos = self.largura - len(esq) - len(dir)
        return esq + ' ' * espacos + dir
    
    def gerar_cupom(self, venda_data):
        """
        Gera cupom de venda com novo layout profissional
        
        Args:
            venda_data: dict com dados da venda
                - id: ID da venda
                - data_venda: timestamp
                - operador: nome do operador
                - items: lista de itens
                - forma_pagamento: forma de pagamento
                - total: valor total
                - valor_recebido: valor recebido
                - troco: troco
                - empresa: dict com dados da empresa (opcional)
        """
        self.buffer = bytearray()
        
        # Inicializa impressora
        self._add(self.INIT)
        self._add(self.ALIGN_CENTER)
        
        empresa = venda_data.get('empresa', {})
        
        # ========== CABEÇALHO DECORATIVO ==========
        self._linha('=')
        
        # ========== NOME EMPRESA ==========
        self._add(self.DOUBLE_SIZE)
        self._add(self.BOLD_ON)
        nome_empresa = empresa.get('nome', 'EMPRESA')
        self._add(self._centralizar(nome_empresa))
        self._add(self.LINE_FEED)
        self._add(self.NORMAL)
        self._add(self.BOLD_OFF)
        
        # ========== DECORATIVO ==========
        self._linha('=')
        
        # ========== DADOS EMPRESA ==========
        self._add(self.ALIGN_CENTER)
        
        if empresa.get('cnpj'):
            self._add(f"CNPJ: {empresa['cnpj']}")
            self._add(self.LINE_FEED)
        
        if empresa.get('endereco'):
            self._add(empresa['endereco'])
            self._add(self.LINE_FEED)
        
        if empresa.get('telefone'):
            self._add(f"Tel: {empresa['telefone']}")
            self._add(self.LINE_FEED)
        
        # ========== SEPARADOR ==========
        self._linha('-')
        
        # ========== TIPO COMPROVANTE ==========
        self._add(self.BOLD_ON)
        self._add(self._centralizar("NAO E CUPOM FISCAL"))
        self._add(self.LINE_FEED)
        self._add(self.BOLD_OFF)
        
        # ========== SEPARADOR ==========
        self._linha('-')
        
        # ========== INFO DA VENDA ==========
        self._add(self.ALIGN_LEFT)
        
        # Formata data/hora
        try:
            dt = datetime.fromisoformat(venda_data['data_venda'])
            data_str = dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            data_str = venda_data['data_venda']
        
        venda_id = venda_data['id']
        # Data e número na mesma linha
        linha_info = f"Data: {data_str}  Venda #{venda_id:06d}"
        self._add(linha_info[:self.largura])
        self._add(self.LINE_FEED)
        
        # Operador
        self._add(f"Operador: {venda_data.get('operador', 'Sistema')}")
        self._add(self.LINE_FEED)
        
        # ========== SEPARADOR ITENS ==========
        self._linha('-')
        
        # ========== CABEÇALHO ITENS ==========
        self._add(self.BOLD_ON)
        cabecalho = " ITEM  DESCRICAO       QTD         VALOR"
        self._add(cabecalho[:self.largura])
        self._add(self.LINE_FEED)
        self._add(self.BOLD_OFF)
        
        # ========== SEPARADOR ITENS ==========
        self._linha('-')
        
        # ========== ITENS ==========
        for idx, item in enumerate(venda_data['items'], 1):
            # Número, descrição e valores em uma linha
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
            
            subtotal = item.get('subtotal', 0)
            sub_str = f"R$ {self._format_brl(subtotal)}"
            
            # Formato: " 01. Descrição       QTD          VALOR"
            linha_item = f" {idx:02d}. {descricao:<16s} {qtd_str:>8s}  {sub_str:>9s}"
            self._add(linha_item[:self.largura])
            self._add(self.LINE_FEED)
        
        # ========== SEPARADOR FINAL ITENS ==========
        self._linha('=')
        
        # ========== TOTAL ==========
        total = venda_data.get('total', 0)
        
        self._add(self.ALIGN_CENTER)
        self._add(self.DOUBLE_HEIGHT)
        self._add(self.BOLD_ON)
        total_str = f"TOTAL: R$ {self._format_brl(total)}"
        self._add(self._centralizar(total_str))
        self._add(self.LINE_FEED)
        self._add(self.NORMAL)
        self._add(self.BOLD_OFF)
        
        # ========== DECORATIVO TOTAL ==========
        self._linha('=')
        
        # ========== PAGAMENTO ==========
        self._add(self.ALIGN_LEFT)
        forma = venda_data.get('forma_pagamento', 'N/A')
        self._add(f"Forma de Pagamento: {forma}")
        self._add(self.LINE_FEED)
        
        # Valor recebido e troco (apenas para dinheiro)
        if forma.lower() == 'dinheiro':
            valor_recebido = venda_data.get('valor_recebido', 0)
            troco = venda_data.get('troco', 0)
            
            recebido_str = self._format_brl(valor_recebido)
            troco_str = self._format_brl(troco)
            
            # Com pontos de preenchimento
            linha_recebido = f"Valor Recebido{('.' * 20)}R$ {recebido_str}"
            self._add(linha_recebido[:self.largura])
            self._add(self.LINE_FEED)
            
            linha_troco = f"Troco{('.' * 28)}R$ {troco_str}"
            self._add(linha_troco[:self.largura])
            self._add(self.LINE_FEED)
        
        # ========== SEPARADOR RODAPÉ ==========
        self._linha('-')
        
        # ========== RODAPÉ ==========
        self._add(self.ALIGN_CENTER)
        
        mensagem = empresa.get('mensagem', 'Obrigado pela preferencia!')
        self._add(self._centralizar(mensagem))
        self._add(self.LINE_FEED)
        
        if empresa.get('site'):
            self._add(self._centralizar(empresa['site']))
            self._add(self.LINE_FEED)
        
        # Data e hora de geração
        gerado_em = datetime.now().strftime('%d/%m %H:%M')
        self._add(self._centralizar(f"Gerado em: {gerado_em}"))
        self._add(self.LINE_FEED)
        
        # ========== DECORATIVO FINAL ==========
        self._linha('=')
        
        self._add(self.LINE_FEED)
        
        # Corta papel
        self._add(self.CUT)
        
        return bytes(self.buffer)
    
    def _format_brl(self, value):
        """Formata valor para BRL"""
        try:
            v = Decimal(str(value))
            s = f"{v:,.2f}"
            s = s.replace(",", "X").replace(".", ",").replace("X", ".")
            return s
        except:
            return "0,00"
    
    def imprimir(self, dados_cupom):
        """
        Envia cupom para impressora
        
        Args:
            dados_cupom: bytes do cupom gerado
            
        Returns:
            bool: True se imprimiu com sucesso
        """
        try:
            sistema = platform.system()
            
            if sistema == 'Windows':
                return self._imprimir_windows(dados_cupom)
            elif sistema == 'Linux':
                return self._imprimir_linux(dados_cupom)
            else:
                print(f"⚠️ Sistema {sistema} não suportado para impressão")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao imprimir: {e}")
            return False
    
    def _imprimir_windows(self, dados):
        """Imprime no Windows"""
        try:
            import win32print
        except ImportError:
            print("❌ Módulo win32print não instalado. Execute: pip install pywin32")
            return False
        
        try:
            # Pega impressora padrão se não especificada
            if not self.printer_name:
                self.printer_name = win32print.GetDefaultPrinter()
            
            # Abre impressora
            printer_handle = win32print.OpenPrinter(self.printer_name)
            
            try:
                # Inicia documento
                job_info = ("Cupom de Venda", None, "RAW")
                job_id = win32print.StartDocPrinter(printer_handle, 1, job_info)
                
                try:
                    win32print.StartPagePrinter(printer_handle)
                    win32print.WritePrinter(printer_handle, dados)
                    win32print.EndPagePrinter(printer_handle)
                finally:
                    win32print.EndDocPrinter(printer_handle)
                
                print(f"✅ Cupom enviado para {self.printer_name}")
                return True
                
            finally:
                win32print.ClosePrinter(printer_handle)
                
        except Exception as e:
            print(f"❌ Erro ao imprimir no Windows: {e}")
            return False
    
    def _imprimir_linux(self, dados):
        """Imprime no Linux"""
        try:
            # Tenta imprimir via lp
            if self.printer_name:
                cmd = f'lp -d {self.printer_name} -o raw'
            else:
                cmd = 'lp -o raw'
            
            import subprocess
            proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
            proc.communicate(input=dados)
            
            if proc.returncode == 0:
                print(f"✅ Cupom enviado para impressora")
                return True
            else:
                print(f"❌ Erro ao enviar cupom (código {proc.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao imprimir no Linux: {e}")
            return False
    
    def listar_impressoras():
        """Lista impressoras disponíveis no sistema"""
        sistema = platform.system()
        
        try:
            if sistema == 'Windows':
                import win32print
                printers = [p[2] for p in win32print.EnumPrinters(2)]
                return printers
            
            elif sistema == 'Linux':
                import subprocess
                result = subprocess.run(['lpstat', '-p'], 
                                      capture_output=True, 
                                      text=True)
                lines = result.stdout.split('\n')
                printers = [line.split()[1] for line in lines if line.startswith('printer')]
                return printers
            
            else:
                return []
                
        except Exception as e:
            print(f"⚠️ Erro ao listar impressoras: {e}")
            return []


# ========== FUNÇÃO AUXILIAR PARA TESTAR ==========
def testar_impressora():
    """Testa impressão com cupom de exemplo"""
    
    dados_teste = {
        'id': 123,
        'data_venda': datetime.now().isoformat(),
        'operador': 'Teste',
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
    
    print("🖨️ Testando impressora...")
    print(f"Impressoras disponíveis: {ThermalPrinter.listar_impressoras()}")
    
    printer = ThermalPrinter()
    cupom = printer.gerar_cupom(dados_teste)
    
    # Salva preview em arquivo
    with open('cupom_preview.txt', 'wb') as f:
        f.write(cupom)
    print("💾 Preview salvo em cupom_preview.txt")
    
    # Tenta imprimir
    if printer.imprimir(cupom):
        print("✅ Cupom impresso com sucesso!")
    else:
        print("❌ Falha ao imprimir")


if __name__ == '__main__':
    testar_impressora()