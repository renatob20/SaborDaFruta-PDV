# utils/cupom_pdf.py
"""
Gerador de PDF com layout de cupom fiscal térmico
Para envio via WhatsApp
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class CupomPDF:
    """Gera PDF no formato de cupom térmico (58mm ou 80mm)"""
    
    def __init__(self, largura_mm=80):
        """
        Args:
            largura_mm: Largura do papel em mm (58 ou 80)
        """
        self.largura_mm = largura_mm
        self.margem_mm = 3
        self.largura_texto_mm = largura_mm - (2 * self.margem_mm)
        
        # Tamanhos de fonte
        self.font_titulo = 12
        self.font_normal = 9
        self.font_small = 7
        self.font_total = 14
    
    def _centralizar_texto(self, c, y, texto, font_size):
        """Centraliza texto na página"""
        text_width = c.stringWidth(texto, "Helvetica-Bold", font_size)
        x = (self.largura_mm * mm_unit - text_width) / 2
        c.drawString(x, y, texto)
        return y - (font_size + 2)  # Espaçamento normal
    
    def _texto_esquerda(self, c, y, texto, font_size=None):
        """Texto alinhado à esquerda"""
        if font_size is None:
            font_size = self.font_normal
        x = self.margem_mm * mm_unit
        c.drawString(x, y, texto)
        return y - (font_size + 2)  # Espaçamento normal
    
    def _linha_dupla(self, c, y, texto1, texto2, font_size=None):
        """Linha com texto à esquerda e direita"""
        if font_size is None:
            font_size = self.font_normal
        
        x_esq = self.margem_mm * mm_unit
        c.drawString(x_esq, y, texto1)
        
        text_width = c.stringWidth(texto2, "Helvetica", font_size)
        x_dir = (self.largura_mm * mm_unit) - text_width - (self.margem_mm * mm_unit)
        c.drawString(x_dir, y, texto2)
        
        return y - (font_size + 2)  # Espaçamento normal
    
  
    def _linha_separadora(self, c, y, tracejada=False, espaco_antes=4, espaco_depois=6):
        """
        Desenha linha separadora sem sobrepor textos
        """
        # desce antes da linha
        y -= espaco_antes

        x1 = self.margem_mm * mm_unit
        x2 = (self.largura_mm - self.margem_mm) * mm_unit

        if tracejada:
           c.setDash(2, 2)
        else:
           c.setDash()

        c.line(x1, y, x2, y)
        c.setDash()
    # desce depois da linha
        return y - espaco_depois
    
    def _linha_decorativa(self, c, y, caractere="="):
        """Desenha linha decorativa com caractere repetido"""
        # Calcula quantos caracteres cabem na largura
        char_width = c.stringWidth(caractere, "Helvetica", self.font_small)
        num_chars = int(self.largura_texto_mm / (char_width / mm_unit))
        linha = caractere * num_chars
        y = self._texto_esquerda(c, y, linha, self.font_small)
        return y

######################################################





    def gerar_cupom(self, dados_venda, output_path=None):
        """
        Gera PDF do cupom
        
        Args:
            dados_venda: Dict com dados da venda (mesmo formato do thermal_printer)
            output_path: Caminho para salvar (opcional)
        
        Returns:
            str: Caminho do arquivo gerado
        """
        
        # Define altura baseada no conteúdo
        altura_estimada = 220 + (len(dados_venda.get('items', [])) * 18)
        
        # Cria arquivo
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            venda_id = dados_venda.get('id', 0)
            output_path = f"cupom_venda_{venda_id}_{timestamp}.pdf"
        
        # Cria canvas
        page_width = self.largura_mm * mm_unit
        page_height = altura_estimada * mm_unit
        
        c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
        
        # Posição inicial (topo)
        y = page_height - (10 * mm_unit)
        
        # ========== CABEÇALHO DECORATIVO ==========
        c.setFont("Helvetica", self.font_small)
        #y = self._linha_decorativa(c, y, "=")
        
        # ========== NOME EMPRESA ==========
        empresa = dados_venda.get('empresa', {})
        c.setFont("Helvetica-Bold", self.font_titulo)
        y = self._centralizar_texto(c, y, empresa.get('nome', 'EMPRESA'), self.font_titulo)
        
        # ========== DECORATIVO ==========
        c.setFont("Helvetica", self.font_small)
        #y = self._linha_decorativa(c, y, "=")
        
        # ========== DADOS EMPRESA ==========
        c.setFont("Helvetica", self.font_small)
        if empresa.get('cnpj'):
            y = self._centralizar_texto(c, y, f"CNPJ: {empresa['cnpj']}", self.font_small)
        if empresa.get('endereco'):
            y = self._centralizar_texto(c, y, empresa['endereco'], self.font_small)
        if empresa.get('telefone'):
            y = self._centralizar_texto(c, y, f"Tel: {empresa['telefone']}", self.font_small)
        
        # ========== SEPARADOR ==========
        y -= 2
        y = self._linha_decorativa(c, y, "-")
        
        # ========== TIPO COMPROVANTE ==========
        c.setFont("Helvetica-Bold", self.font_normal)
        y = self._centralizar_texto(c, y, "NÃO É CUPOM FISCAL", self.font_normal)
        
        # ========== SEPARADOR ==========
        y -= 1
        y = self._linha_decorativa(c, y, "-")
        
        # ========== INFO DA VENDA ==========
        c.setFont("Helvetica", self.font_small)
        
        # Data/Hora
        data_venda = dados_venda.get('data_venda', datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(data_venda.replace(' ', 'T'))
            data_fmt = dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            data_fmt = data_venda
        
        # Número da venda
        venda_id = dados_venda.get('id', 0)
        
        # Data e número na mesma linha
        linha_info = f"Data: {data_fmt}     Venda #{venda_id:06d}"
        y = self._texto_esquerda(c, y, linha_info, self.font_small)
        
        # Operador
        operador = dados_venda.get('operador', 'Sistema')
        y = self._texto_esquerda(c, y, f"Operador: {operador}", self.font_small)
        
        # ========== SEPARADOR ITENS ==========
        y -= 1
        y = self._linha_decorativa(c, y, "-")
        
        # ========== CABEÇALHO ITENS ==========
        c.setFont("Helvetica-Bold", self.font_small)
        y = self._texto_esquerda(c, y, " ITEM  DESCRIÇÃO           QTD         VALOR", self.font_small)
        
        # ========== SEPARADOR ITENS ==========
        y = self._linha_decorativa(c, y, "-")
        
        # ========== ITENS ==========
        c.setFont("Helvetica", self.font_small)
        
        items = dados_venda.get('items', [])
        for idx, item in enumerate(items, 1):
            # Número, descrição e valores em uma linha
            tipo = item.get('tipo', '')
            sabor = item.get('sabor', '') or item.get('produto_nome', '')
            descricao = f"{tipo}" if not sabor else f"{tipo} {sabor}"
            
            qtd = item.get('quantidade')
            peso = item.get('peso_kg')
            valor_unit = item.get('valor_unit', 0.0)
            subtotal = item.get('subtotal', 0.0)
            
            if qtd:
                qtd_str = f"{qtd}un"
            elif peso:
                qtd_str = f"{peso:.3f}kg"
            else:
                qtd_str = "1un"
            
            valor_unit_str = f"R${valor_unit:.2f}".replace('.', ',')
            subtotal_str = f"R${subtotal:.2f}".replace('.', ',')
            
            # Limita descrição para 16 caracteres (garante 1 linha)
            descricao = descricao[:16]
            
            # Formato: " 01. Descrição       QTD          VALOR"
            linha_item = f" {idx:02d}. {descricao:<16s} {qtd_str:>8s}  {subtotal_str:>9s}"
            y = self._texto_esquerda(c, y, linha_item, self.font_small)
        
        # ========== SEPARADOR FINAL ITENS ==========
        y = self._linha_decorativa(c, y, "=")
        
        # ========== TOTAL ==========
        total = dados_venda.get('total', 0.0)
        total_str = f"R$ {total:.2f}".replace('.', ',')
        
        y -= 4
        c.setFont("Helvetica-Bold", self.font_total)
        y = self._linha_dupla(c, y, "TOTAL", total_str, self.font_total)
        
        # ========== DECORATIVO TOTAL ==========
        y -= 2
        c.setFont("Helvetica", self.font_small)
        y = self._linha_decorativa(c, y, "=")
        
        # ========== PAGAMENTO ==========
        y -= 2
        c.setFont("Helvetica", self.font_normal)
        
        forma_pag = dados_venda.get('forma_pagamento', 'N/A')
        y = self._texto_esquerda(c, y, f"Forma de Pagamento: {forma_pag}", self.font_normal)
        
        if forma_pag == "Dinheiro":
            valor_recebido = dados_venda.get('valor_recebido', 0.0)
            troco = dados_venda.get('troco', 0.0)
            
            recebido_str = f"R$ {valor_recebido:.2f}".replace('.', ',')
            troco_str = f"R$ {troco:.2f}".replace('.', ',')
            
            # Com pontos de preenchimento
            linha_recebido = f"Valor Recebido{('.' * 25)}{recebido_str}"
            y = self._texto_esquerda(c, y, linha_recebido[:int(self.largura_texto_mm)], self.font_normal)
            
            linha_troco = f"Troco{('.' * 30)}{troco_str}"
            y = self._texto_esquerda(c, y, linha_troco[:int(self.largura_texto_mm)], self.font_normal)
        
        # ========== SEPARADOR RODAPÉ ==========
        y -= 2
        y = self._linha_decorativa(c, y, "-")
        
        # ========== RODAPÉ ==========
        y -= 2
        c.setFont("Helvetica-Bold", self.font_small)
        
        mensagem = empresa.get('mensagem', 'Obrigado pela preferência!')
        y = self._centralizar_texto(c, y, mensagem, self.font_small)
        
        if empresa.get('site'):
            c.setFont("Helvetica", self.font_small)
            y = self._centralizar_texto(c, y, empresa['site'], self.font_small)
        
        c.setFont("Helvetica", self.font_small - 1)
        y = self._centralizar_texto(c, y, 
            f"Gerado em: {datetime.now().strftime('%d/%m %H:%M')}", 
            self.font_small - 1)
        
        # ========== DECORATIVO FINAL ==========
        y -= 2
        c.setFont("Helvetica", self.font_small)
        y = self._linha_decorativa(c, y, "=")
        
        # ========== FINALIZA ==========
        c.save()
        
        return output_path


# ========== TESTE ==========
if __name__ == "__main__":
    # Dados de teste
    dados_teste = {
        'id': 123,
        'data_venda': '2024-12-25 15:30:00',
        'operador': 'João Silva',
        'forma_pagamento': 'Dinheiro',
        'total': 35.50,
        'valor_recebido': 50.00,
        'troco': 14.50,
        'items': [
            {
                'tipo': 'Açaí',
                'sabor': 'Tradicional',
                'quantidade': None,
                'peso_kg': 0.500,
                'valor_unit': 45.00,
                'subtotal': 22.50
            },
            {
                'tipo': 'Picolé',
                'sabor': 'Morango',
                'quantidade': 2,
                'peso_kg': None,
                'valor_unit': 5.00,
                'subtotal': 10.00
            },
            {
                'tipo': 'Sorvete',
                'sabor': 'Chocolate',
                'quantidade': None,
                'peso_kg': 0.150,
                'valor_unit': 20.00,
                'subtotal': 3.00
            }
        ],
        'empresa': {
            'nome': 'SABOR DA FRUTA',
            'cnpj': '12.345.678/0001-90',
            'endereco': 'Rua Exemplo, 123 - Centro',
            'telefone': '(11) 98765-4321',
            'mensagem': 'Obrigado pela preferência!',
            'site': 'www.sabordafruta.com.br'
        }
    }
    
    gerador = CupomPDF(largura_mm=80)
    arquivo = gerador.gerar_cupom(dados_teste, "cupom_teste.pdf")
    
    print(f"✅ PDF gerado: {arquivo}")
    print("Abrindo arquivo...")
    
    import os
    os.startfile(arquivo)  # Windows