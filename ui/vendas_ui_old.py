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


# ============ ADICIONAR ESTA LINHA ============
from utils.data_sync import SimpleFlagSync
# ==============================================

# use a função de conexão do módulo de products (mesmo DB_PATH)
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

# ----------------- DB init (garante tabelas essenciais para vendas) -----------------
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

    # Verifica se coluna 'total' existe na tabela vendas; se não, adiciona.
    cur.execute("PRAGMA table_info(vendas);")
    cols = [r[1] for r in cur.fetchall()]  # r[1] é o nome da coluna
    if "total" not in cols:
        try:
            cur.execute("ALTER TABLE vendas ADD COLUMN total REAL DEFAULT 0.0;")
        except Exception:
            pass

    conn.commit()
    conn.close()

# ---------- Fim PARTE A ----------

# ---------- PARTE B: UI builder (layout) ----------
class VendasUI(ttk.Window):
    def __init__(self, display_name="Admin", role="admin"):
        super().__init__(themename="superhero")
    
    # ===== PRIMEIRO: Define atributos =====
        self.display_name = display_name
        self.role = role
        self.operador = display_name  # Alias para compatibilidade
        self.sync = SimpleFlagSync()
    
    # ===== SEGUNDO: Inicializa dados =====
        self.produtos = []          # lista de rows (id, nome, tipo, sabor, preco, estoque)
        self.produtos_cache = {}    # chave exibida -> dict {id,nome,tipo,sabor,preco,estoque}
        self.carrinho = []          # lista de itens dict
        self.total = 0.0
    
    # ===== TERCEIRO: Configurações da janela =====
        self.title(f"📋 Vendas - {self.operador}")
        self.minsize(1000, 640)
    
    # Tenta abrir maximizado se possível
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass
    
    # ===== QUARTO: Garante tabelas =====
        ensure_tables()
    
    # ===== QUINTO: Constrói interface =====
        self._build_ui()
    
    # ===== SEXTO: Carrega dados =====
        self._load_produtos()            # ← NOME CORRETO
        self._carregar_vendas_recentes()
    
    # ===== SÉTIMO: Inicia monitoramento =====
        self._iniciar_monitoramento()
        print("🔄 Monitoramento de produtos iniciado")
    
        # ===================================


    def _build_ui(self):
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        # header
        header = ttk.Frame(container)
        header.pack(fill=X, pady=(0, 8))
        ttk.Label(header, text="Registrar Venda", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        #ttk.Label(header, text=f"Operador: {self.operador}", font=("Segoe UI", 10)).pack(side=RIGHT)

        main = ttk.Frame(container)
        main.pack(fill=BOTH, expand=True)

        # left main area (selection + carrinho)
        left = ttk.Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,8))

        # selection frame
        sel_frame = ttk.Labelframe(left, text="Adicionar Item", padding=8)
        sel_frame.pack(fill=X)

        # Tipo
        ttk.Label(sel_frame, text="Tipo:").grid(row=0, column=0, sticky=W, padx=6, pady=6)
        self.tipo_cb = ttk.Combobox(sel_frame, values=[], state="readonly", width=30)
        self.tipo_cb.grid(row=0, column=1, sticky=W, padx=6)
        # evento: ao mudar o tipo carregamos apenas produtos desse tipo
        self.tipo_cb.bind("<<ComboboxSelected>>", lambda e: self._on_tipo_selected())

        # Produto (exibe apenas o nome, sem preço)
        ttk.Label(sel_frame, text="Produto:").grid(row=1, column=0, sticky=W, padx=6, pady=6)
        self.produto_cb = ttk.Combobox(sel_frame, values=[], state="readonly", width=50)
        self.produto_cb.grid(row=1, column=1, sticky=W, padx=6)
        self.produto_cb.bind("<<ComboboxSelected>>", lambda e: self._on_produto_selected())

        # quantidade
        ttk.Label(sel_frame, text="Qtd (unid):").grid(row=2, column=0, sticky=W, padx=6, pady=6)
        self.qtd_var = StringVar()
        self.qtd_entry = ttk.Entry(sel_frame, textvariable=self.qtd_var, width=12)
        self.qtd_entry.grid(row=2, column=1, sticky=W, padx=6)

        # peso (kg)
        ttk.Label(sel_frame, text="Peso (kg):").grid(row=3, column=0, sticky=W, padx=6, pady=6)
        self.peso_var = StringVar()
        self.peso_entry = ttk.Entry(sel_frame, textvariable=self.peso_var, width=12, state="disabled")
        self.peso_entry.grid(row=3, column=1, sticky=W, padx=6)

        # valor unitario (readonly, pequeno) - visível mas não editável (vai puxar do DB)
        ttk.Label(sel_frame, text="Valor Unit (R$):").grid(row=4, column=0, sticky=W, padx=6, pady=6)
        self.valor_unit_var = StringVar(value=brl_format(0.0))
        self.valor_unit_entry = ttk.Entry(sel_frame, textvariable=self.valor_unit_var, width=14, state="readonly")
        self.valor_unit_entry.grid(row=4, column=1, sticky=W, padx=6)

        # adicionar
        ttk.Button(sel_frame, text="➕ Adicionar ao carrinho", bootstyle=SUCCESS, command=self.adicionar_ao_carrinho)\
            .grid(row=5, column=0, columnspan=2, pady=10)

        # carrinho frame
        cart_frame = ttk.Labelframe(left, text="Carrinho", padding=8)
        cart_frame.pack(fill=BOTH, expand=True, pady=(8,0))

        cols = ("idx", "produto", "tipo", "qtd", "peso_kg", "unit", "subtotal")
        self.tree_cart = ttk.Treeview(cart_frame, columns=cols, show="headings", selectmode="browse")
        headings = {
            "idx": "ID",
            "produto": "Produto",
            "tipo": "Tipo",
            "qtd": "Qtd",
            "peso_kg": "Peso(kg)",
            "unit": "R$/Unid",
            "subtotal": "Subtotal"
        }
        for c in cols:
            self.tree_cart.heading(c, text=headings[c], anchor="center")
            w = 60 if c == "idx" else 140
            self.tree_cart.column(c, anchor="center", width=w)
        self.tree_cart.pack(fill=BOTH, expand=True, side=LEFT)
        sb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree_cart.yview)
        self.tree_cart.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)

        # ações do carrinho
        cart_actions = ttk.Frame(left)
        cart_actions.pack(fill=X, pady=8)
        ttk.Button(cart_actions, text="✏️ Editar item", command=self.editar_item).pack(side=LEFT, padx=6)
        ttk.Button(cart_actions, text="🗑️ Remover item", bootstyle=DANGER, command=self.remover_item).pack(side=LEFT, padx=6)
        ttk.Button(cart_actions, text="🔄 Limpar carrinho", bootstyle=SECONDARY, command=self.limpar_carrinho).pack(side=RIGHT, padx=6)

        # right side: resumo + últimas vendas
        right = ttk.Frame(main, width=360)
        right.pack(side=RIGHT, fill=Y)

        resumo = ttk.Labelframe(right, text="Resumo da Venda", padding=8)
        resumo.pack(fill=X)

        ttk.Label(resumo, text="Total (R$):").grid(row=0, column=0, sticky=W, padx=6, pady=6)
        self.total_var = StringVar(value=brl_format(0.0))
        self.total_entry = ttk.Entry(resumo, textvariable=self.total_var, width=20, state="readonly")
        self.total_entry.grid(row=0, column=1, padx=6)

        ttk.Label(resumo, text="Forma de Pagamento:").grid(row=1, column=0, sticky=W, padx=6, pady=6)
        self.forma_cb = ttk.Combobox(resumo, values=["Pix", "Crédito", "Débito", "Dinheiro"], state="readonly", width=16)
        self.forma_cb.grid(row=1, column=1, padx=6)
        self.forma_cb.bind("<<ComboboxSelected>>", lambda e: self._on_forma_change())

        ttk.Label(resumo, text="Valor Recebido (R$):").grid(row=2, column=0, sticky=W, padx=6, pady=6)
        self.recebido_var = StringVar(value=brl_format(0.0))
        # Recebido sempre habilitado (como solicitado)
        self.recebido_entry = ttk.Entry(resumo, textvariable=self.recebido_var, width=20)
        self.recebido_entry.grid(row=2, column=1, padx=6)
        self.recebido_entry.bind("<KeyRelease>", lambda e: self._atualizar_troco())

        ttk.Label(resumo, text="Troco (R$):").grid(row=3, column=0, sticky=W, padx=6, pady=6)
        self.troco_var = StringVar(value=brl_format(0.0))
        self.troco_entry = ttk.Entry(resumo, textvariable=self.troco_var, width=20, state="readonly")
        self.troco_entry.grid(row=3, column=1, padx=6)

        ttk.Button(resumo, text="✔️ Finalizar Venda", bootstyle=SUCCESS, command=self._finalizar_venda).grid(row=4, column=0, columnspan=2, pady=12)
        ttk.Button(resumo, text="🔙 Sair", bootstyle=INFO, command=self.voltar_dashboard).grid(row=5, column=0, columnspan=2)

        # últimas vendas
        recent = ttk.Labelframe(right, text="Últimas Vendas", padding=8)
        recent.pack(fill=BOTH, expand=True, pady=8)
        self.tree_recent = ttk.Treeview(recent, columns=("id","data","total","operador"), show="headings", height=8)
        self.tree_recent.heading("id", text="ID", anchor="center")
        self.tree_recent.heading("data", text="Data", anchor="center")
        self.tree_recent.heading("total", text="Total R$", anchor="center")
        self.tree_recent.heading("operador", text="Operador", anchor="center")
        self.tree_recent.column("id", width=50, anchor="center")
        self.tree_recent.column("data", width=160, anchor="center")
        self.tree_recent.column("total", width=90, anchor="center")
        self.tree_recent.column("operador", width=100, anchor="center")
        self.tree_recent.pack(fill=BOTH, expand=True)

# ---------- Fim PARTE B ----------

# ---------- PARTE C: lógica (carregamento, carrinho, finalização, voltar) ----------

    # ---------------- carregamento de produtos ----------
    def _load_produtos(self):
        """
        Carrega todos os produtos e popula:
          - self.produtos (lista de rows)
          - self.tipo_cb com os tipos distintos (campo 'tipo' da tabela)
        Observação: não preenche produto_cb aqui — produto_cb é preenchido ao selecionar um tipo.
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, nome, tipo, sabor, preco, estoque FROM produtos ORDER BY tipo, nome")
            rows = cur.fetchall()
            conn.close()
            self.produtos = rows

            # Tipos distintos vindos diretamente do resultado (garante correspondência com o DB)
            tipos = sorted({r[2] for r in rows if r[2]})
            self.tipo_cb['values'] = tipos

            # Monta cache indexado por uma chave única (nome ou nome (id:X) caso haja duplicatas)
            self.produtos_cache.clear()
            name_count = {}
            for r in rows:
                pid, nome, tipo, sabor, preco, estoque = r
                base = nome or f"produto_{pid}"
                # se houver nomes repetidos, criamos chave única com id
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

            # limpa seleção atual (produto_cb será preenchido quando o tipo for escolhido)
            self.produto_cb.set("")
            self.produto_cb['values'] = []
        except Exception as e:
            logging.exception("Erro ao carregar produtos:")
            messagebox.showerror("Erro", f"Falha ao carregar produtos: {e}")



    def _iniciar_monitoramento(self):
            """Verifica mudanças na tabela de produtos a cada 5 segundos"""
            try:
                if self.sync.check_change('produtos'):
                    print("📦 Produtos atualizados! Recarregando...")

                    # Salva o tipo selecionado atual
                    tipo_atual = self.tipo_cb.get()

                    self._load_produtos()

                    # Se havia um tipo selecionado, reaplica a filtragem
                    if tipo_atual:
                        self.tipo_cb.set(tipo_atual)
                        self._on_tipo_selected()  # ← Atualiza combo de produtos
                        print(f"✅ Produtos do tipo '{tipo_atual}' atualizados!")


            except Exception as e:
                print(f"⚠️ Erro ao verificar mudanças: {e}")
    
            self.after(5000, self._iniciar_monitoramento)   


    # ---------------- evento tipo selecionado ----------------
    def _on_tipo_selected(self):
        tipo = self.tipo_cb.get().strip()
        if not tipo:
            # limpa produto combo
            self.produto_cb.set("")
            self.produto_cb['values'] = []
            return

        # FILTRA produtos no cache por campo 'tipo' (garante que vem do DB)
        values = []
        for key, info in self.produtos_cache.items():
            if (info.get('tipo') or "").strip() == tipo:
                values.append(key)

        # ordena alfabeticamente para melhor UX
        values = sorted(values, key=lambda k: self.produtos_cache[k]['nome'].lower())

        self.produto_cb['values'] = values

        # habilita/desabilita campos qtd/peso conforme tipo (SORVETE usa peso)
        if tipo.lower() == "sorvete":
            self.peso_entry.config(state="normal")
            self.qtd_entry.config(state="disabled")
            self.qtd_var.set("")
        else:
            self.peso_entry.config(state="disabled")
            self.peso_var.set("")
            self.qtd_entry.config(state="normal")

        # auto selecionar o primeiro produto disponível (opcional)
        if values:
            self.produto_cb.current(0)
            self._on_produto_selected()
        else:
            self.produto_cb.set("")
            self.valor_unit_var.set(brl_format(0.0))

    # ---------------- evento produto selecionado ----------------
    def _on_produto_selected(self):
        key = self.produto_cb.get()
        if not key:
            self.valor_unit_var.set(brl_format(0.0))
            return

        info = self.produtos_cache.get(key)
        if not info:
            # caso não encontre, tenta procurar por nome simples (compatibilidade)
            info = next((v for v in self.produtos_cache.values() if v.get('nome') == key), None)
            if not info:
                self.valor_unit_var.set(brl_format(0.0))
                return

        preco = float(info.get("preco", 0.0))
        self.valor_unit_var.set(brl_format(preco))

        # se o produto é sorvete, habilita peso, senão qtd — (duplica segurança)
        tipo = (info.get("tipo") or "").lower()
        if tipo == "sorvete":
            self.peso_entry.config(state="normal")
            self.qtd_entry.config(state="disabled")
            self.qtd_var.set("")
        else:
            self.peso_entry.config(state="disabled")
            self.peso_var.set("")
            self.qtd_entry.config(state="normal")

    # ---------------- adicionar ao carrinho ----------------
    def adicionar_ao_carrinho(self):
        key = self.produto_cb.get()
        if not key:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        info = self.produtos_cache.get(key)
        if not info:
            messagebox.showerror("Erro", "Produto não encontrado no cache.")
            return
        tipo = info.get("tipo", "")
        nome = info.get("nome")
        pid = info.get("id")
        preco = float(info.get("preco", 0.0))

        if tipo.lower() == "sorvete":
            peso = parse_peso_kg_input(self.peso_var.get())
            
            if peso <= 0:
                messagebox.showwarning("Atenção", "Informe um peso válido (kg).")
                return
            quantidade = None
            subtotal = round(peso * preco, 2)
        else:
            try:
                quantidade = int(self.qtd_var.get())
            except Exception:
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
            "quantidade": quantidade,
            "peso_kg": peso,
            "valor_unit": preco,
            "subtotal": subtotal
        }
        self.carrinho.append(item)
        self._refresh_carrinho()
        self._recalcular_total()
        # limpa campos
        self.qtd_var.set("")
        self.peso_var.set("")

    def _refresh_carrinho(self):
        # limpa tree
        for r in self.tree_cart.get_children():
            self.tree_cart.delete(r)
        # repopula
        for idx, it in enumerate(self.carrinho):
            self.tree_cart.insert("", "end", iid=str(idx), values=(
                idx + 1,
                it["produto_nome"],
                it["tipo"],
                it["quantidade"] if it["quantidade"] is not None else "",
                f"{it['peso_kg']:.3f}" if it["peso_kg"] is not None else "",
                brl_format(it["valor_unit"]),
                brl_format(it["subtotal"])
            ))

    def _recalcular_total(self):
        total = sum(it["subtotal"] for it in self.carrinho)
        self.total = float(total)
        self.total_var.set(brl_format(self.total))
        # atualiza troco automaticamente conforme recebido
        self._atualizar_troco()

    # ---------------- editar / remover item ----------------
    def editar_item(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um item para editar.")
            return
        idx = int(sel[0])
        item = self.carrinho.pop(idx)
        # tenta selecionar produto correspondente no combo (busca por id)
        key = next((k for k,v in self.produtos_cache.items() if v['id'] == item["produto_id"]), None)
        if key:
            self.produto_cb.set(key)
            self._on_produto_selected()
        # preenche campos
        if item["tipo"].lower() == "sorvete":
            self.peso_var.set(str(item["peso_kg"] or ""))
            self.qtd_var.set("")
            self.peso_entry.config(state="normal")
            self.qtd_entry.config(state="disabled")
        else:
            self.qtd_var.set(str(item["quantidade"] or ""))
            self.peso_var.set("")
            self.qtd_entry.config(state="normal")
            self.peso_entry.config(state="disabled")
        # atualiza view
        self._refresh_carrinho()
        self._recalcular_total()

    def remover_item(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um item para remover.")
            return
        idx = int(sel[0])
        self.carrinho.pop(idx)
        self._refresh_carrinho()
        self._recalcular_total()

    def limpar_carrinho(self):
        if not self.carrinho:
            return
        if messagebox.askyesno("Confirmar", "Deseja limpar o carrinho?"):
            self.carrinho.clear()
            self._refresh_carrinho()
            self._recalcular_total()

    # ---------------- pagamento / troco ----------------
    def _on_forma_change(self):
        forma = self.forma_cb.get()
        # Valor recebido ALWAYS enabled (requested). Troco only active for Dinheiro.
        # Recebido já está sempre habilitado por design.
        if forma == "Dinheiro":
            # troco é mostrado e será calculado automaticamente
            self._atualizar_troco()
        else:
            # other payments, troco stays 0
            self.troco_var.set(brl_format(0.0))

    def _atualizar_troco(self):
        try:
            recebido = parse_brl_to_float(self.recebido_var.get())
            if self.forma_cb.get() == "Dinheiro":
                troco = max(0.0, recebido - self.total)
            else:
                troco = 0.0
            self.troco_var.set(brl_format(troco))
        except Exception:
            self.troco_var.set(brl_format(0.0))

    # ---------------- finalizar venda ----------------
    def _finalizar_venda(self):
        """Finaliza a venda e grava no banco."""
        try:
            # valida dados
            tipo_produto = (self.tipo_cb.get() or "").strip()
            forma_pagamento = (self.forma_cb.get() or "").strip()  # ✅ CORRIGIDO: forma_cb, não pagamento_var
            valor_recebido_str = (self.recebido_var.get() or "0").strip()  # ✅ CORRIGIDO: recebido_var, não valor_recebido_var
            
            if not tipo_produto:
                messagebox.showwarning("Atenção", "Selecione um tipo de produto.")
                return
            
            if not forma_pagamento:
                messagebox.showwarning("Atenção", "Selecione a forma de pagamento.")
                return
            
            # valida itens no carrinho
            if not self.carrinho:
                messagebox.showwarning("Atenção", "Carrinho vazio.")
                return
            
            # calcula totais
            valor_recebido = parse_brl_to_float(valor_recebido_str)  # ✅ usa a função helper
            total = parse_brl_to_float(self.total_var.get())  # ✅ usa a função helper
            troco = valor_recebido - total
            
            # grava na tabela vendas
            conn = get_connection()
            cur = conn.cursor()
            


            timestamp = datetime.now().isoformat(sep=" ")
            
            # INSERT com TODOS os campos obrigatórios
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
                tipo_produto,
                forma_pagamento,
                total,
                valor_recebido,
                troco,
                timestamp,
                self.operador or "operador"
            ))
            
            venda_id = cur.lastrowid
            
            # grava itens do carrinho
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

            # ===== ADICIONAR ESTAS 2 LINHAS =====
            self.sync.notify_change('produtos')
            print("✅ Estoque atualizado")
            # ====================================
    
            conn.close()
            
            messagebox.showinfo(
                "Sucesso",
                f"Venda #{venda_id} gravada com sucesso!\n\nTotal: R$ {total:.2f}\nTroco: R$ {troco:.2f}"
            )
            
            # limpa formulário
            self._limpar_carrinho()
            self._resetar_campos()
            
        except Exception as e:
            logging.exception("Erro ao finalizar venda:")
            messagebox.showerror("Erro", f"Falha ao gravar venda: {e}")
        

    def _limpar_carrinho(self):
        """Limpa o carrinho."""
        self.carrinho.clear()
        self._refresh_carrinho()
        self._recalcular_total()
    
    def _resetar_campos(self):
        """Reseta todos os campos após finalizar venda."""
        self.tipo_cb.set("")
        self.produto_cb.set("")
        self.qtd_var.set("")
        self.peso_var.set("")
        self.valor_unit_var.set(brl_format(0.0))
        self.recebido_var.set(brl_format(0.0))
        self.troco_var.set(brl_format(0.0))
        self.forma_cb.set("")
        self._carregar_vendas_recentes()  # atualiza listagem de últimas vendas
       
    # ---------------- carregar ultimas vendas ----------------
    def _carregar_vendas_recentes(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, data_venda, total, operador FROM vendas ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
            conn.close()
            for r in self.tree_recent.get_children():
                self.tree_recent.delete(r)
            for r in rows:
                self.tree_recent.insert("", "end", values=(r[0], r[1], brl_format(r[2]), r[3]))
        except Exception:
            pass

    # ---------------- voltar ao dashboard ----------------
    def voltar_dashboard(self):
        # chama o dashboard em um processo separado e fecha esta janela
        dashboard_script = os.path.join(ROOT, "ui", "dashboard_ui.py")
        try:
            subprocess.Popen([sys.executable, dashboard_script, self.display_name, self.role], close_fds=True)
        except Exception:
            # fallback simples caso Popen falhe, tenta chamar via os.system
            os.system(f'"{sys.executable}" "{dashboard_script}" "{self.display_name}" "{self.role}"')
        # fecha apenas esta janela; o novo processo continua rodando
        self.destroy()

# ---------- Fim PARTE C ----------
if __name__ == "__main__":
    app = VendasUI("Admin", "admin")
    app.mainloop()


#execução direta para testes
# if __name__ == "__main__":
#     import sys
    
#     # obtém argumentos passados via linha de comando (do dashboard)
#     operador = sys.argv[1] if len(sys.argv) > 1 else "Operador"
#     role = sys.argv[2] if len(sys.argv) > 2 else "operador"
    
#     # cria janela root (mainloop próprio)
#     root = ttk.Window(themename="superhero")
#     root.withdraw()  # oculta a root invisível
    
#     # cria janela de vendas como filha
#     win = VendasUI(master=root, operador=operador, role=role)
#     #win.transient(root)
    
#     def on_close():
#         win.destroy()
#         root.destroy()
    
#     win.protocol("WM_DELETE_WINDOW", on_close)
#     #root.deiconify()
#     root.mainloop()
