# ---------- PARTE A: imports, helpers, ensure_tables ----------
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
from tkinter import messagebox, StringVar

# garante que imports relativos funcionem quando executado diretamente
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.data_sync import SimpleFlagSync
from database.db import get_connection

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

# ----------------- Helpers -----------------
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
    """
    Aceita entradas:
      - '0.100' → 0.100 kg
      - '100' → 0.100 kg (interpreta como gramas)
      - '100g' → 0.100 kg
      - '0,100' → 0.100 kg
    Retorna float em KG.
    """
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

    # se usuário digitou GRAMAS (ex: 100 → 100g)
    if val >= 10:
        return val / 1000.0

    return val

# ----------------- DB init -----------------
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

    # Verifica coluna 'total'
    cur.execute("PRAGMA table_info(vendas);")
    cols = [r[1] for r in cur.fetchall()]
    if "total" not in cols:
        try:
            cur.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0.0;")
        except Exception:
            pass

    conn.commit()
    conn.close()

# ---------- Fim PARTE A ----------

# ---------- PARTE B: UI builder (NOVO LAYOUT ESTILO CUPOM) ----------
class VendasUI(ttk.Window):
    def __init__(self, display_name="Admin", role="admin"):
        super().__init__(themename="superhero")
        
        # ---- Maximiza a Janela (Comportamento padrão para Windows) ----
        try:
            self.state("zoomed")
        except Exception:
            # Fallback para sistemas Windows onde 'zoomed' não está disponível
            # ou em casos muito específicos.
            self.attributes("-zoomed", True)


        # Atributos
        self.display_name = display_name
        self.role = role
        self.operador = display_name
        self.sync = SimpleFlagSync()
        self.produtos = []
        self.produtos_cache = {}
        self.carrinho = []
        self.total = 0.0
        
        # Janela
        self.title(f"📋 PDV - Vendas - {self.operador}")
        self.minsize(900, 650)
        
        try:
            self.state("zoomed")
        except:
            try:
                self.attributes("-zoomed", True)
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
        main_container = ttk.Frame(self, padding=15)
        main_container.pack(fill=BOTH, expand=True)
        
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
        
        # Tabela com colunas do print (sem COD)
        cols = ("tipo", "sabor", "qtd", "peso", "valor_unit", "subtotal")
        self.tree_cart = ttk.Treeview(cupom_frame, columns=cols, show="headings", 
                                      selectmode="browse", height=12)
        
        # Cabeçalhos
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
        
        # Botões de ação do carrinho
        cart_btns = ttk.Frame(cupom_frame)
        cart_btns.pack(fill=X, pady=(8, 0))
        ttk.Button(cart_btns, text="🗑️ Remover Item", bootstyle=DANGER, 
                  command=self.remover_item).pack(side=LEFT, padx=5)
        ttk.Button(cart_btns, text="🔄 Limpar Tudo", bootstyle=SECONDARY, 
                  command=self.limpar_carrinho).pack(side=LEFT, padx=5)
        
        # ========== SEÇÃO INFERIOR: PAGAMENTO ==========
        pagamento_frame = ttk.Frame(main_container)
        pagamento_frame.pack(fill=X)
        
        # Coluna esquerda: Forma de Pagamento
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
        
        # Coluna direita: Valores
        col_right = ttk.Frame(pagamento_frame)
        col_right.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # VALOR TOTAL (destaque verde como no print)
        total_frame = ttk.Frame(col_right, bootstyle=SUCCESS)
        total_frame.pack(fill=X, pady=3)
        
        ttk.Label(total_frame, text="Valor Total", 
                 font=("Segoe UI", 12, "bold")).pack(side=LEFT, padx=10)
        self.total_var = StringVar(value="R$ 0,00")
        ttk.Label(total_frame, textvariable=self.total_var, 
                 font=("Segoe UI", 16, "bold"), 
                 bootstyle=SUCCESS).pack(side=RIGHT, padx=10)
        
        # VALOR RECEBIDO
        recebido_frame = ttk.Frame(col_right)
        recebido_frame.pack(fill=X, pady=3)
        
        ttk.Label(recebido_frame, text="Valor Recebido", 
                 font=("Segoe UI", 11)).pack(side=LEFT, padx=10)
        
        self.recebido_var = StringVar(value="0,00")
        
        self.recebido_entry = ttk.Entry(recebido_frame, textvariable=self.recebido_var, 
                                   width=15, font=("Segoe UI", 12))
        
        self.recebido_entry.pack(side=RIGHT, padx=10)

        # Bind para eventos de foco e digitação
        self.recebido_entry.bind("<FocusIn>", self._on_recebido_focus_in)
        self.recebido_entry.bind("<FocusOut>", self._on_recebido_focus_out)
        self.recebido_entry.bind("<KeyRelease>", self._on_recebido_key)

        
        #recebido_entry.bind("<KeyRelease>", lambda e: self._atualizar_troco())
        
        # TROCO
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
        
        ttk.Button(botoes_finais, text="✅ FINALIZAR VENDA", bootstyle=SUCCESS, 
                  command=self._finalizar_venda, width=20).pack(side=RIGHT, padx=5)
        ttk.Button(botoes_finais, text="🔙 Voltar ao Menu", bootstyle=INFO, 
                  command=self.voltar_dashboard, width=15).pack(side=RIGHT, padx=5)

    # ---------- PARTE C: Lógica (mantém os métodos atuais) ----------
    
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
        """Filtra produtos por tipo e mostra apenas o sabor"""
        tipo = self.tipo_cb.get().strip()
        if not tipo:
            self.produto_cb.set("")
            self.produto_cb['values'] = []
            return

        values = []
        for key, info in self.produtos_cache.items():
            if (info.get('tipo') or "").strip() == tipo:
                sabor = info.get('sabor', '').strip()
                if sabor:
                    display_name = sabor
                else:
                    display_name = info.get('nome', key)
                values.append(display_name)

        values = sorted(values, key=lambda x: x.lower())
        self.produto_cb['values'] = values

        if tipo.lower() == "sorvete" or tipo.lower() == "açaí/sorvete":
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
            self.valor_unit_var.set("R$ 0,00")

    def _on_produto_selected(self):
        """Atualiza valor unitário ao selecionar produto"""
        sabor_selecionado = self.produto_cb.get()
        if not sabor_selecionado:
            self.valor_unit_var.set("R$ 0,00")
            return

        tipo_atual = self.tipo_cb.get().strip()
        info = None
        
        for key, produto_info in self.produtos_cache.items():
            if produto_info.get('tipo') == tipo_atual:
                sabor = produto_info.get('sabor', '').strip()
                if sabor == sabor_selecionado:
                    info = produto_info
                    break
                elif not sabor and produto_info.get('nome') == sabor_selecionado:
                    info = produto_info
                    break
        
        if not info:
            self.valor_unit_var.set("R$ 0,00")
            return

        preco = float(info.get("preco", 0.0))
        self.valor_unit_var.set(f"R$ {brl_format(preco)}")

    def adicionar_ao_carrinho(self):
        """Adiciona item ao carrinho"""
        sabor_selecionado = self.produto_cb.get()
        if not sabor_selecionado:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        
        tipo_atual = self.tipo_cb.get().strip()
        info = None
        
        for key, produto_info in self.produtos_cache.items():
            if produto_info.get('tipo') == tipo_atual:
                sabor = produto_info.get('sabor', '').strip()
                if sabor == sabor_selecionado:
                    info = produto_info
                    break
                elif not sabor and produto_info.get('nome') == sabor_selecionado:
                    info = produto_info
                    break
        
        if not info:
            messagebox.showerror("Erro", "Produto não encontrado.")
            return
        
        tipo = info.get("tipo", "")
        nome = info.get("nome")
        sabor = info.get("sabor", "")
        pid = info.get("id")
        preco = float(info.get("preco", 0.0))

        if tipo.lower() in ["sorvete", "açaí/sorvete"]:
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
            # Mostra o sabor ou nome
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
        """Limpa campo ao clicar se estiver com valor padrão"""
        valor = self.recebido_var.get()
        if valor in ["0,00", "R$ 0,00"]:
            self.recebido_var.set("")


    def _on_recebido_focus_out(self, event):
        """Formata valor ao sair do campo"""
        valor = self.recebido_var.get().strip()
        if not valor or valor == "":
            self.recebido_var.set("0,00")
        else:
        # Já formata com a máscara
            try:
                valor_float = parse_brl_to_float(valor)
                self.recebido_var.set(brl_format(valor_float))
            except:
                self.recebido_var.set("0,00")
    
        self._atualizar_troco()

    def _on_recebido_key(self, event):
        """Formata valor enquanto digita (apenas números)"""
        # Ignora teclas especiais
        if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab']:
            self._atualizar_troco()
            return
    
     # Pega apenas números do que foi digitado
        valor = self.recebido_var.get()
        apenas_numeros = ''.join(filter(str.isdigit, valor))
    
        if not apenas_numeros:
            self.recebido_var.set("")
            self._atualizar_troco()
            return
    
     # Converte para centavos e formata
        try:
            centavos = int(apenas_numeros)
            valor_float = centavos / 100.0
        
            # Formata como moeda (sem R$)
            valor_formatado = f"{valor_float:.2f}".replace(".", ",")
        
            self.recebido_var.set(valor_formatado)
        
            # Posiciona cursor no final
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
                    tipo_produto, 
                    forma_pagamento, 
                    total, 
                    valor_recebido, 
                    troco, 
                    data_venda, 
                    operador
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
                        venda_id, 
                        produto_id, 
                        produto_nome,
                        tipo,
                        quantidade, 
                        peso_kg,
                        preco_unitario, 
                        subtotal
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
            
            self.sync.notify_change('produtos')
            print("✅ Venda finalizada - estoque atualizado")
            
            conn.close()
            
            messagebox.showinfo(
                "Sucesso",
                f"Venda #{venda_id} finalizada!\n\n" +
                f"Total: R$ {total:.2f}\n" +
                f"Recebido: R$ {valor_recebido:.2f}\n" +
                f"Troco: R$ {troco:.2f}"
            )
            
            self._limpar_venda()
            
        except Exception as e:
            logging.exception("Erro ao finalizar venda:")
            messagebox.showerror("Erro", f"Falha ao gravar venda: {e}")

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
        dashboard_script = os.path.join(ROOT, "ui", "dashboard_ui.py")
        try:
            subprocess.Popen([sys.executable, dashboard_script, self.display_name, self.role], close_fds=True)
        except Exception:
        # fallback simples caso Popen falhe
            os.system(f'"{sys.executable}" "{dashboard_script}" "{self.display_name}" "{self.role}"')
    # fecha apenas esta janela; o novo processo continua rodando
        self.destroy()


if __name__ == "__main__":
    app = VendasUI("Admin", "admin")
    app.mainloop()