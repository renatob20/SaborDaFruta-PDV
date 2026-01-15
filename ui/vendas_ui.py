# ---------- IMPORTS ----------
import os
import sys
import sqlite3
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
import subprocess

# GUI
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, filedialog

# garante que imports relativos funcionem
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.data_sync import SimpleFlagSync
from database.db import get_connection

# Importação condicional da impressora
try:
    from utils.thermal_printer import ThermalPrinter
    IMPRESSORA_DISPONIVEL = True
except ImportError:
    IMPRESSORA_DISPONIVEL = False
    print("⚠️ Módulo de impressão térmica não disponível")

# Importação do gerador de PDF
try:
    from utils.cupom_pdf import CupomPDF
    PDF_DISPONIVEL = True
except ImportError:
    PDF_DISPONIVEL = False
    print("⚠️ Módulo de PDF não disponível (instale: pip install reportlab)")


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

# ---------- FUNÇÕES AUXILIARES ----------
def brl_format(value):
    """Formata float/Decimal -> '1.234,56' (BRL style)."""
    try:
        v = Decimal(value)
    except (InvalidOperation, TypeError):
        v = Decimal("0.00")
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def parse_brl_to_float(value):
    """Converte string BRL '1.234,56' -> float 1234.56"""
    if not value:
        return 0.0
    s = str(value).strip().replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0

def parse_peso_kg_input(text):
    """Aceita '0.100', '100', '100g', '0,100' e retorna float em KG."""
    if not text:
        return 0.0
    s = str(text).strip().lower().replace(" ", "")
    if s.endswith("g"):
        s = s[:-1]
    s = s.replace(",", ".")
    try:
        val = float(s)
    except:
        return 0.0
    if val >= 10:
        return val / 1000.0
    return val

def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_produto TEXT,
            data_venda TEXT NOT NULL,
            operador TEXT,
            forma_pagamento TEXT,
            valor_recebido REAL,
            troco REAL,
            total REAL DEFAULT 0.0
        );
    """)
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
    cur.execute("PRAGMA table_info(vendas);")
    cols = [r[1] for r in cur.fetchall()]
    if "total" not in cols:
        try:
            cur.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0.0;")
        except Exception:
            pass
    conn.commit()
    conn.close()

# ---------- CLASSE PRINCIPAL ----------
class VendasUI(ttk.Frame):
    def __init__(self,master, display_name="Admin", role="admin"):
        super().__init__(master)
        self.master = master
        self.pack(fill=BOTH, expand=True)
        
        # Atributos
        self.display_name = display_name
        self.role = role
        self.operador = display_name
        self.sync = SimpleFlagSync()
        self.produtos = []
        self.produtos_cache = {}
        self.carrinho = []
        self.total = 0.0
        
        # Atributos para impressão
        self.ultima_venda_id = None
        self.ultima_venda_data = None
        self.btn_imprimir = None
        
               
        try:
            self.master.state("zoomed")
        except:
            try:
                self.master.attributes("-zoomed", True)
            except:
                pass
        
        # Setup
        ensure_tables()
        self._build_ui()
        self._load_produtos()
        self._carregar_vendas_recentes()
        self._iniciar_monitoramento()
        print("🔄 Monitoramento iniciado")

    def _build_ui(self):
        """Layout estilo cupom fiscal"""
                        
        # Container principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_container, style="Dark.TFrame")
        header_frame.pack(fill=X, padx=0, pady=0)
        
        ttk.Label(header_frame, text="📋 Vendas de produtos",
        font=("Segoe UI", 18, "bold"), 
        foreground="#FFFFFF").pack(pady=10)
        
        # Separador
        separator = ttk.Frame(header_frame, height=2, style="success.TFrame")
        separator.pack(fill=X, padx=50, pady=(0, 10))

        


        
        # ========== SEÇÃO SUPERIOR: SELEÇÃO DE PRODUTOS ==========
        selecao_frame = ttk.Labelframe(main_container, text="ADICIONAR PRODUTO", padding=12)
        selecao_frame.pack(fill=X, pady=(0, 10))
        
        # Linha 1: Tipo e Produto
        row1 = ttk.Frame(selecao_frame)
        row1.pack(fill=X, pady=5)
        
        ttk.Label(row1, text="Tipo:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 8))
        self.tipo_cb = ttk.Combobox(row1, values=[], state="readonly", width=18)
        self.tipo_cb.pack(side=LEFT, padx=(0, 20))
        self.tipo_cb.bind("<<ComboboxSelected>>", lambda e: self._on_tipo_selected())
        
        ttk.Label(row1, text="Produto:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 8))
        self.produto_cb = ttk.Combobox(row1, values=[], state="readonly", width=30)
        self.produto_cb.pack(side=LEFT, padx=(0, 20))
        self.produto_cb.bind("<<ComboboxSelected>>", lambda e: self._on_produto_selected())
        
        # Linha 2: Quantidade/Peso e Valor Unitário
        row2 = ttk.Frame(selecao_frame)
        row2.pack(fill=X, pady=5)
        
        ttk.Label(row2, text="Qtd:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 8))
        self.qtd_var = StringVar()
        self.qtd_entry = ttk.Entry(row2, textvariable=self.qtd_var, width=10)
        self.qtd_entry.pack(side=LEFT, padx=(0, 20))
        
        ttk.Label(row2, text="Peso (kg):", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 8))
        self.peso_var = StringVar()
        self.peso_entry = ttk.Entry(row2, textvariable=self.peso_var, width=10, state="disabled")
        self.peso_entry.pack(side=LEFT, padx=(0, 20))
        
        ttk.Label(row2, text="Valor Unit:", font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 8))
        self.valor_unit_var = StringVar(value="R$ 0,00")
        ttk.Entry(row2, textvariable=self.valor_unit_var, width=12, state="readonly").pack(side=LEFT, padx=(0, 20))
        
        ttk.Button(row2, text="➕ ADICIONAR", bootstyle=SUCCESS, 
                  command=self.adicionar_ao_carrinho, width=15).pack(side=LEFT, padx=20)
        
        # ========== SEÇÃO CENTRAL: TABELA ESTILO CUPOM ==========
        cupom_frame = ttk.Labelframe(main_container, text="CUPOM DE VENDA", padding=10)
        cupom_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        cols = ("tipo", "sabor", "qtd", "peso", "valor_unit", "subtotal")
        self.tree_cart = ttk.Treeview(cupom_frame, columns=cols, show="headings", 
                                      selectmode="browse", height=12)
        
        headers = {
            "tipo": "TIPO PRODUTO",
            "sabor": "SABOR",
            "qtd": "QTD",
            "peso": "PESO (KG)",
            "valor_unit": "VALOR UNIT",
            "subtotal": "SUBTOTAL"
        }
        
        widths = {
            "tipo": 150,
            "sabor": 150,
            "qtd": 80,
            "peso": 100,
            "valor_unit": 120,
            "subtotal": 120
        }
        
        for c in cols:
            self.tree_cart.heading(c, text=headers[c], anchor=CENTER)
            self.tree_cart.column(c, anchor=CENTER, width=widths[c])
        
        self.tree_cart.pack(fill=BOTH, expand=True, side=LEFT)
        
        sb = ttk.Scrollbar(cupom_frame, orient="vertical", command=self.tree_cart.yview)
        self.tree_cart.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)
        
        cart_btns = ttk.Frame(cupom_frame)
        cart_btns.pack(fill=X, pady=(8, 0))
        ttk.Button(cart_btns, text="🗑️ Remover Item", bootstyle=DANGER, 
                  command=self.remover_item).pack(side=LEFT, padx=5)
        ttk.Button(cart_btns, text="🔄 Limpar Tudo", bootstyle=SECONDARY, 
                  command=self.limpar_carrinho).pack(side=LEFT, padx=5)
        
        # ========== SEÇÃO INFERIOR: PAGAMENTO ==========
        pagamento_frame = ttk.Frame(main_container)
        pagamento_frame.pack(fill=X)
        
        col_left = ttk.Frame(pagamento_frame)
        col_left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        forma_lbl = ttk.Label(col_left, text="Forma de Pagamento", 
                             font=("Segoe UI", 11, "bold"))
        forma_lbl.pack(anchor=W, pady=(0, 5))
        
        self.forma_cb = ttk.Combobox(col_left, 
                                     values=["Débito", "Crédito", "Pix", "Dinheiro"], 
                                     state="readonly", width=20, font=("Segoe UI", 12))
        self.forma_cb.pack(anchor=W)
        self.forma_cb.bind("<<ComboboxSelected>>", lambda e: self._on_forma_change())
        
        col_right = ttk.Frame(pagamento_frame)
        col_right.pack(side=RIGHT, fill=BOTH, expand=True)
        
        total_frame = ttk.Frame(col_right, bootstyle=SUCCESS)
        total_frame.pack(fill=X, pady=3)
        
        ttk.Label(total_frame, text="Valor Total", 
                 font=("Segoe UI", 12, "bold")).pack(side=LEFT, padx=10)
        self.total_var = StringVar(value="R$ 0,00")
        ttk.Label(total_frame, textvariable=self.total_var, 
                 font=("Segoe UI", 16, "bold"), 
                 bootstyle=SUCCESS).pack(side=RIGHT, padx=10)
        
        recebido_frame = ttk.Frame(col_right)
        recebido_frame.pack(fill=X, pady=3)
        
        ttk.Label(recebido_frame, text="Valor Recebido", 
                 font=("Segoe UI", 11)).pack(side=LEFT, padx=10)
        
        self.recebido_var = StringVar(value="0,00")
        self.recebido_entry = ttk.Entry(recebido_frame, textvariable=self.recebido_var, 
                                   width=15, font=("Segoe UI", 12))
        self.recebido_entry.pack(side=RIGHT, padx=10)
        self.recebido_entry.bind("<FocusIn>", self._on_recebido_focus_in)
        self.recebido_entry.bind("<FocusOut>", self._on_recebido_focus_out)
        self.recebido_entry.bind("<KeyRelease>", self._on_recebido_key)
        
        troco_frame = ttk.Frame(col_right)
        troco_frame.pack(fill=X, pady=3)
        
        ttk.Label(troco_frame, text="Troco", 
                 font=("Segoe UI", 11)).pack(side=LEFT, padx=10)
        self.troco_var = StringVar(value="R$ 0,00")
        ttk.Label(troco_frame, textvariable=self.troco_var, 
                 font=("Segoe UI", 12, "bold")).pack(side=RIGHT, padx=10)
        
        # ========== BOTÕES FINAIS ==========
        botoes_finais = ttk.Frame(main_container)
        botoes_finais.pack(fill=X, pady=(10, 0))
        
        # Botão IMPRIMIR sempre visível (oferece escolha entre térmico e PDF)
        self.btn_imprimir = ttk.Button(
            botoes_finais, 
            text="🖨️ IMPRIMIR CUPOM", 
            bootstyle="INFO",
            command=self._escolher_tipo_impressao, 
            width=23,
            state="disabled"
        )
        self.btn_imprimir.pack(side=RIGHT, padx=5)
        
        ttk.Button(botoes_finais, text="✅ FINALIZAR VENDA", bootstyle=SUCCESS, 
                  command=self._finalizar_venda, width=20).pack(side=RIGHT, padx=5)
        ttk.Button(botoes_finais, text="🔙 VOLTAR MENU", bootstyle=INFO, 
                  command=self.voltar_dashboard, width=20).pack(side=RIGHT, padx=5)

    def _load_produtos(self):
        """Carrega produtos do banco"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, nome, tipo, sabor, preco, estoque FROM produtos ORDER BY tipo, nome")
            rows = cur.fetchall()
            conn.close()
            self.produtos = rows

            tipos = sorted({r[2] for r in rows if r[2]})
            self.tipo_cb['values'] = tipos

            self.produtos_cache.clear()
            name_count = {}
            for r in rows:
                pid, nome, tipo, sabor, preco, estoque = r
                base = nome or f"produto_{pid}"
                count = name_count.get(base, 0)
                name_count[base] = count + 1
                key = base if count == 0 else f"{base} (id:{pid})"
                self.produtos_cache[key] = {
                    "id": pid,
                    "nome": nome,
                    "tipo": tipo,
                    "sabor": sabor,
                    "preco": float(preco or 0.0),
                    "estoque": estoque
                }

            self.produto_cb.set("")
            self.produto_cb['values'] = []
        except Exception as e:
            logging.exception("Erro ao carregar produtos:")
            messagebox.showerror("Erro", f"Falha ao carregar produtos: {e}")

    def _iniciar_monitoramento(self):
        """Monitora mudanças nos produtos"""
        try:
            if self.sync.check_change('produtos'):
                print("📦 Produtos atualizados! Recarregando...")
                tipo_atual = self.tipo_cb.get()
                self._load_produtos()
                if tipo_atual:
                    self.tipo_cb.set(tipo_atual)
                    self._on_tipo_selected()
                    print(f"✅ Produtos do tipo '{tipo_atual}' atualizados!")
        except Exception as e:
            print(f"⚠️ Erro ao verificar mudanças: {e}")
        
        self.after(5000, self._iniciar_monitoramento)

    def _on_tipo_selected(self):
        """Filtra produtos por tipo e atualiza preço"""
        tipo = self.tipo_cb.get().strip()
        if not tipo:
            self.produto_cb.set("")
            self.produto_cb['values'] = []
            return

        values = []
        preco_tipo = None
        
        for key, info in self.produtos_cache.items():
            if (info.get('tipo') or "").strip() == tipo:
                sabor = info.get('sabor')
                sabor = sabor.strip() if sabor else ""
                
                if not sabor:
                    display_name = info.get('nome', tipo)
                    preco_tipo = info.get('preco', 0.0)
                else:
                    display_name = sabor
                
                values.append(display_name)

        values = sorted(values, key=lambda x: x.lower())
        self.produto_cb['values'] = values

        if tipo.lower() in ["sorvete", "açaí/sorvete", "açaí", "sorvete"]:
            self.peso_entry.config(state="normal")
            self.qtd_entry.config(state="disabled")
            self.qtd_var.set("")
        else:
            self.peso_entry.config(state="disabled")
            self.peso_var.set("")
            self.qtd_entry.config(state="normal")

        if values:
            self.produto_cb.current(0)
            self._on_produto_selected()
        else:
            self.produto_cb.set("")
            if preco_tipo:
                self.valor_unit_var.set(f"R$ {brl_format(preco_tipo)}")
            else:
                self.valor_unit_var.set("R$ 0,00")

    def _on_produto_selected(self):
        """Atualiza valor unitário ao selecionar produto"""
        produto_selecionado = self.produto_cb.get()
        if not produto_selecionado:
            self.valor_unit_var.set("R$ 0,00")
            return

        tipo_atual = self.tipo_cb.get().strip()
        info = None
        
        for key, produto_info in self.produtos_cache.items():
            if produto_info.get('tipo') == tipo_atual:
                sabor = produto_info.get('sabor')
                sabor = sabor.strip() if sabor else ""
                nome = produto_info.get('nome', '')
                
                if (sabor and sabor == produto_selecionado) or (nome == produto_selecionado):
                    info = produto_info
                    break
        
        if info:
            preco = float(info.get("preco", 0.0))
            self.valor_unit_var.set(f"R$ {brl_format(preco)}")
        else:
            self.valor_unit_var.set("R$ 0,00")

    def adicionar_ao_carrinho(self):
        """Adiciona item ao carrinho"""
        produto_selecionado = self.produto_cb.get()
        if not produto_selecionado:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        
        tipo_atual = self.tipo_cb.get().strip()
        info = None
        
        for key, produto_info in self.produtos_cache.items():
            if produto_info.get('tipo') == tipo_atual:
                sabor = produto_info.get('sabor')
                sabor = sabor.strip() if sabor else ""
                nome = produto_info.get('nome', '')
                
                if (sabor and sabor == produto_selecionado) or (nome == produto_selecionado):
                    info = produto_info
                    break
        
        if not info:
            messagebox.showerror("Erro", "Produto não encontrado.")
            return
        
        tipo = info.get("tipo", "")
        nome = info.get("nome")
        sabor = info.get("sabor")
        sabor = sabor if sabor else ""
        pid = info.get("id")
        preco = float(info.get("preco", 0.0))

        if tipo.lower() in ["sorvete", "açaí/sorvete", "açaí"]:
            peso = parse_peso_kg_input(self.peso_var.get())
            if peso <= 0:
                messagebox.showwarning("Atenção", "Informe um peso válido.")
                return
            quantidade = None
            subtotal = round(peso * preco, 2)
        else:
            try:
                quantidade = int(self.qtd_var.get())
            except:
                quantidade = 0
            if quantidade <= 0:
                messagebox.showwarning("Atenção", "Informe uma quantidade válida.")
                return
            peso = None
            subtotal = round(quantidade * preco, 2)

        item = {
            "produto_id": pid,
            "produto_nome": nome,
            "tipo": tipo,
            "sabor": sabor,
            "quantidade": quantidade,
            "peso_kg": peso,
            "valor_unit": preco,
            "subtotal": subtotal
        }
        self.carrinho.append(item)
        self._refresh_carrinho()
        self._recalcular_total()
        self.qtd_var.set("")
        self.peso_var.set("")

    def _refresh_carrinho(self):
        """Atualiza exibição do carrinho"""
        for r in self.tree_cart.get_children():
            self.tree_cart.delete(r)
        
        for idx, it in enumerate(self.carrinho):
            display_sabor = it.get("sabor", "") or it.get("produto_nome", "")
            
            self.tree_cart.insert("", "end", iid=str(idx), values=(
                it["tipo"],
                display_sabor,
                it["quantidade"] if it["quantidade"] is not None else "",
                f"{it['peso_kg']:.3f}" if it["peso_kg"] is not None else "",
                f"R$ {brl_format(it['valor_unit'])}",
                f"R$ {brl_format(it['subtotal'])}"
            ))

    def _recalcular_total(self):
        """Recalcula total"""
        total = sum(it["subtotal"] for it in self.carrinho)
        self.total = float(total)
        self.total_var.set(f"R$ {brl_format(self.total)}")
        self._atualizar_troco()

    def remover_item(self):
        """Remove item selecionado"""
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um item para remover.")
            return
        idx = int(sel[0])
        self.carrinho.pop(idx)
        self._refresh_carrinho()
        self._recalcular_total()

    def limpar_carrinho(self):
        """Limpa carrinho"""
        if not self.carrinho:
            return
        if messagebox.askyesno("Confirmar", "Deseja limpar o carrinho?"):
            self.carrinho.clear()
            self._refresh_carrinho()
            self._recalcular_total()

    def _on_forma_change(self):
        """Atualiza troco conforme forma de pagamento"""
        if self.forma_cb.get() == "Dinheiro":
            self._atualizar_troco()
        else:
            self.troco_var.set("R$ 0,00")

    def _atualizar_troco(self):
        """Calcula troco"""
        try:
            recebido = parse_brl_to_float(self.recebido_var.get())
            if self.forma_cb.get() == "Dinheiro":
                troco = max(0.0, recebido - self.total)
            else:
                troco = 0.0
            self.troco_var.set(f"R$ {brl_format(troco)}")
        except:
            self.troco_var.set("R$ 0,00")

    def _on_recebido_focus_in(self, event):
        """Limpa campo ao clicar"""
        valor = self.recebido_var.get()
        if valor in ["0,00", "R$ 0,00"]:
            self.recebido_var.set("")

    def _on_recebido_focus_out(self, event):
        """Formata valor ao sair do campo"""
        valor = self.recebido_var.get().strip()
        if not valor:
            self.recebido_var.set("0,00")
        else:
            try:
                valor_float = parse_brl_to_float(valor)
                self.recebido_var.set(brl_format(valor_float))
            except:
                self.recebido_var.set("0,00")
        self._atualizar_troco()

    def _on_recebido_key(self, event):
        """Formata valor enquanto digita"""
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab']:
            self._atualizar_troco()
            return
        
        valor = self.recebido_var.get()
        apenas_numeros = ''.join(filter(str.isdigit, valor))
        
        if not apenas_numeros:
            self.recebido_var.set("")
            self._atualizar_troco()
            return
        
        try:
            centavos = int(apenas_numeros)
            valor_float = centavos / 100.0
            valor_formatado = f"{valor_float:.2f}".replace(".", ",")
            self.recebido_var.set(valor_formatado)
            self.recebido_entry.icursor(len(valor_formatado))
        except:
            pass
        
        self._atualizar_troco()

    def _finalizar_venda(self):
        """Finaliza venda"""
        try:
            tipo_produto = (self.tipo_cb.get() or "").strip()
            forma_pagamento = (self.forma_cb.get() or "").strip()
            valor_recebido_str = (self.recebido_var.get() or "0").strip()
            
            if not forma_pagamento:
                messagebox.showwarning("Atenção", "Selecione a forma de pagamento.")
                return
            
            if not self.carrinho:
                messagebox.showwarning("Atenção", "Carrinho vazio.")
                return
            
            valor_recebido = parse_brl_to_float(valor_recebido_str)
            total = self.total
            troco = valor_recebido - total
            
            conn = get_connection()
            cur = conn.cursor()
            
            timestamp = datetime.now().isoformat(sep=" ")
            
            cur.execute("""
                INSERT INTO vendas (
                    tipo_produto, forma_pagamento, total, 
                    valor_recebido, troco, data_venda, operador
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                tipo_produto or "Diversos",
                forma_pagamento,
                total,
                float(valor_recebido or 0.0),
                float(troco or 0.0),
                timestamp,
                self.operador
            ))
            
            venda_id = cur.lastrowid
            
            for item in self.carrinho:
                cur.execute("""
                    INSERT INTO venda_items (
                        venda_id, produto_id, produto_nome, tipo,
                        quantidade, peso_kg, preco_unitario, subtotal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    venda_id,
                    item.get("produto_id", 0),
                    item.get("produto_nome", ""),
                    item.get("tipo", ""),
                    item.get("quantidade"),
                    item.get("peso_kg"),
                    item.get("valor_unit", 0.0),
                    item.get("subtotal", 0.0)
                ))
            
            conn.commit()
            conn.close()
            
            # Salva dados para impressão
            self.ultima_venda_id = venda_id
            self.ultima_venda_data = {
                'id': venda_id,
                'data_venda': timestamp,
                'operador': self.operador,
                'forma_pagamento': forma_pagamento,
                'total': total,
                'valor_recebido': valor_recebido,
                'troco': troco,
                'items': self.carrinho.copy(),
                'empresa': {
                    'nome': 'AÇAITERIA O SABOR DA FRUTA',
                    'cnpj': '13.215.869/0001-03',
                    'endereco': 'Estrada do pau ferro, pitomba',
                    'telefone': '(75) 98187-7711',
                    'mensagem': 'Obrigado pela preferencia!',
                    'Instagran': '@acaiteriasabordafruta_'
                }
            }
            
            if self.btn_imprimir:
                self.btn_imprimir.config(state="normal")
            
            self.sync.notify_change('produtos')
            print("✅ Venda finalizada")
            
            msg_sucesso = (
                f"Venda #{venda_id} finalizada!\n\n"
                f"Total: R$ {total:.2f}\n"
                f"Recebido: R$ {valor_recebido:.2f}\n"
                f"Troco: R$ {troco:.2f}\n\n"
                f"Clique em 'IMPRIMIR CUPOM' para escolher\n"
                f"entre impressão térmica ou gerar PDF."
            )
            
            messagebox.showinfo("Sucesso", msg_sucesso)
            self._limpar_venda()
            
        except Exception as e:
            logging.exception("Erro ao finalizar venda:")
            messagebox.showerror("Erro", f"Falha ao gravar venda: {e}")

    def _escolher_tipo_impressao(self):
        """Mostra diálogo para escolher entre impressão térmica ou PDF"""
        if not self.ultima_venda_id or not self.ultima_venda_data:
            messagebox.showwarning("Atenção", "Nenhuma venda para imprimir.")
            return
        
        # Cria janela de escolha
        escolha = ttk.Toplevel(self)
        escolha.title("Escolha o Tipo de Cupom")
        escolha.geometry("550x380")
        escolha.resizable(False, False)
        
        # Centraliza janela
        escolha.update_idletasks()
        x = (escolha.winfo_screenwidth() // 2) - (550 // 2)
        y = (escolha.winfo_screenheight() // 2) - (380 // 2)
        escolha.geometry(f"+{x}+{y}")
        
        # Container
        container = ttk.Frame(escolha, padding=30)
        container.pack(fill=BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(
            container,
            text="🖨️ Como deseja o cupom?",
            font=("Segoe UI", 18, "bold")
        )
        titulo.pack(pady=(0, 10))
        
        subtitulo = ttk.Label(
            container,
            text=f"Venda #{self.ultima_venda_id:06d} - Total: R$ {self.ultima_venda_data['total']:.2f}",
            font=("Segoe UI", 11)
        )
        subtitulo.pack(pady=(0, 30))
        
        # Frame dos botões
        botoes_frame = ttk.Frame(container)
        botoes_frame.pack(fill=BOTH, expand=True)
        
        # ========== BOTÃO 1: IMPRESSORA TÉRMICA ==========
        if IMPRESSORA_DISPONIVEL:
            frame_termico = ttk.Frame(botoes_frame)
            frame_termico.pack(side=LEFT, padx=10, fill=BOTH, expand=True)
            
            btn_termico = ttk.Button(
                frame_termico,
                text="🖨️\n\nIMPRESSORA\nTÉRMICA\n\n(Imprimir)",
                bootstyle="primary",
                command=lambda: [escolha.destroy(), self._imprimir_termico()],
                width=20
            )
            btn_termico.pack(fill=BOTH, expand=True, pady=5)
            
            ttk.Label(
                frame_termico,
                text="Imprimir direto\nna impressora térmica",
                font=("Segoe UI", 9),
                foreground="gray"
            ).pack(pady=5)
        
        # ========== BOTÃO 2: GERAR PDF ==========
        if PDF_DISPONIVEL:
            frame_pdf = ttk.Frame(botoes_frame)
            frame_pdf.pack(side=LEFT, padx=10, fill=BOTH, expand=True)
            
            btn_pdf = ttk.Button(
                frame_pdf,
                text="📄\n\nGERAR\nPDF\n\n(WhatsApp)",
                bootstyle="success",
                command=lambda: [escolha.destroy(), self._gerar_pdf()],
                width=20
            )
            btn_pdf.pack(fill=BOTH, expand=True, pady=5)
            
            ttk.Label(
                frame_pdf,
                text="Salva PDF para enviar\npelo WhatsApp",
                font=("Segoe UI", 9),
                foreground="gray"
            ).pack(pady=5)
        
        # Botão Cancelar
        ttk.Button(
            container,
            text="Cancelar",
            bootstyle="secondary",
            command=escolha.destroy,
            width=20
        ).pack(pady=(20, 0))
        
        # Torna modal
        escolha.transient(self)
        escolha.grab_set()

    def _gerar_pdf(self):
        """Gera PDF do cupom para enviar pelo WhatsApp"""
        if not PDF_DISPONIVEL:
            messagebox.showwarning(
                "Aviso", 
                "Gerador de PDF não disponível.\n\nInstale: pip install reportlab"
            )
            return
        
        try:
            # Sugere nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_sugerido = f"cupom_venda_{self.ultima_venda_id:06d}_{timestamp}.pdf"
            
            # Pergunta onde salvar
            caminho = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
                initialfile=nome_sugerido,
                title="Salvar Cupom PDF"
            )
            
            if not caminho:  # Usuário cancelou
                return
            
            # Gera PDF
            gerador = CupomPDF(largura_mm=80)
            arquivo_gerado = gerador.gerar_cupom(
                self.ultima_venda_data,
                output_path=caminho
            )
            
            print(f"📄 PDF gerado: {arquivo_gerado}")
            
            # Pergunta se quer abrir
            resposta = messagebox.askyesno(
                "PDF Gerado!",
                f"✅ Cupom PDF gerado com sucesso!\n\n"
                f"📂 Local: {os.path.basename(arquivo_gerado)}\n\n"
                f"Deseja abrir o arquivo agora?"
            )
            
            if resposta:
                # Abre o PDF
                if sys.platform == 'win32':
                    os.startfile(arquivo_gerado)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', arquivo_gerado])
                else:  # Linux
                    subprocess.call(['xdg-open', arquivo_gerado])
            
            # Desabilita botão e limpa dados
            if self.btn_imprimir:
                self.btn_imprimir.config(state="disabled")
            self.ultima_venda_id = None
            self.ultima_venda_data = None
            
            messagebox.showinfo(
                "Pronto!",
                f"📱 Agora você pode:\n\n"
                f"1. Abrir o WhatsApp Web\n"
                f"2. Selecionar o contato do cliente\n"
                f"3. Clicar no 📎 (anexar)\n"
                f"4. Enviar o arquivo PDF\n\n"
                f"💚 Cupom digital - sem papel!"
            )
        
        except Exception as e:
            logging.exception("Erro ao gerar PDF:")
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {e}")

    def _imprimir_termico(self):
        """Imprime cupom na impressora térmica"""
        if not IMPRESSORA_DISPONIVEL:
            messagebox.showwarning(
                "Aviso", 
                "Impressora térmica não disponível.\n\nInstale: pip install pywin32"
            )
            return
        
        try:
            printer = ThermalPrinter()
            cupom_bytes = printer.gerar_cupom(self.ultima_venda_data)
            
            preview_path = os.path.join(ROOT, f"cupom_venda_{self.ultima_venda_id}.txt")
            with open(preview_path, 'wb') as f:
                f.write(cupom_bytes)
            print(f"💾 Preview salvo em: {preview_path}")
            
            if printer.imprimir(cupom_bytes):
                messagebox.showinfo(
                    "Sucesso",
                    f"✅ Cupom da venda #{self.ultima_venda_id} enviado para impressora!"
                )
                
                if self.btn_imprimir:
                    self.btn_imprimir.config(state="disabled")
                self.ultima_venda_id = None
                self.ultima_venda_data = None
            else:
                messagebox.showerror(
                    "Erro de Impressão",
                    f"Não foi possível imprimir o cupom.\n\n"
                    f"Preview salvo em:\n{preview_path}\n\n"
                    f"Verifique se a impressora está conectada."
                )
        
        except Exception as e:
            logging.exception("Erro ao imprimir cupom:")
            messagebox.showerror("Erro", f"Falha ao imprimir: {e}")

    def _limpar_venda(self):
        """Limpa formulário após venda"""
        self.carrinho.clear()
        self._refresh_carrinho()
        self._recalcular_total()
        self.tipo_cb.set("")
        self.produto_cb.set("")
        self.qtd_var.set("")
        self.peso_var.set("")
        self.valor_unit_var.set("R$ 0,00")
        self.recebido_var.set("0,00")
        self.troco_var.set("R$ 0,00")
        self.forma_cb.set("")

    def _carregar_vendas_recentes(self):
        """Carrega últimas vendas (se precisar)"""
        pass

    def voltar_dashboard(self):
        """Volta para dashboard"""
        self.destroy()
        from ui.dashboard_ui import DashboardUI
        DashboardUI(master=self.master,
                    display_name=self.display_name,
                    role=self.role)