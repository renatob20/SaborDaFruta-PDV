# ui/produtos_ui.py
import os
import sys

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.data_sync import SimpleFlagSync

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar

from models.produto_model import (
    criar_tabela_produtos,
    inserir_produto,
    listar_produtos,
    atualizar_produto,
    excluir_produto
)


class ProdutosUI(ttk.Frame):
    """Tela de Produtos - Mesmo padrão de VendasUI"""
    
    def __init__(self, master, display_name="Admin", role="admin"):
        super().__init__(master)  # ← PRIMEIRO
        self.master = master
        self.pack(fill=BOTH, expand=True)  # ← DEPOIS
        
        # Atributos
        self.display_name = display_name
        self.role = role
        self.sync = SimpleFlagSync()
        self.selected_id = None
        
        # Variáveis
        self.nome_tipo = StringVar()
        self.sabor = StringVar()
        self.preco = StringVar()
        self.estoque = StringVar()
        
        # Maximiza janela
        try:
            self.master.state("zoomed")
        except:
            try:
                self.master.attributes("-zoomed", True)
            except:
                pass
        
        # Inicializa tabela
        criar_tabela_produtos()
        
        # Constrói UI
        self._build_ui()
        self._carregar_produtos()

    def _build_ui(self):
        """Constrói interface"""
        
        # Container principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # ========== HEADER ==========
        header_frame = ttk.Frame(main_container, style="Dark.TFrame")
        header_frame.pack(fill=X, padx=0, pady=0)
        
        ttk.Label(
            header_frame, 
            text="📦 Gerenciamento de Produtos",
            font=("Segoe UI", 18, "bold"), 
            foreground="#FFFFFF"
        ).pack(pady=10)
        
        # Separador
        separator = ttk.Frame(header_frame, height=2, style="success.TFrame")
        separator.pack(fill=X, padx=50, pady=(0, 10))
              
        # ========== FORMULÁRIO ==========
        form_frame = ttk.Labelframe(main_container, text="Cadastro de Produto", padding=15)
        form_frame.pack(fill=X, pady=(10, 0))
        
        # Grid 2 colunas
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        
        # Linha 1: Tipo e Preço
        ttk.Label(form_frame, text="Tipo:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=W, padx=(0, 10), pady=8
        )
        
        self.tipo_entry = ttk.Entry(form_frame, textvariable=self.nome_tipo, width=32)
        self.tipo_entry.grid(row=0, column=1, sticky=W, padx=(0, 20), pady=8)
        
        # Placeholder
        self.tipo_placeholder = "Ex: Picolé, Sorvete, Bebida, etc."
        if not self.nome_tipo.get():
            self.nome_tipo.set(self.tipo_placeholder)
            self.tipo_entry.config(foreground='gray')
        
        def on_tipo_focus_in(event):
            if self.nome_tipo.get() == self.tipo_placeholder:
                self.nome_tipo.set('')
                self.tipo_entry.config(foreground='white')
        
        def on_tipo_focus_out(event):
            if not self.nome_tipo.get():
                self.nome_tipo.set(self.tipo_placeholder)
                self.tipo_entry.config(foreground='gray')
        
        self.tipo_entry.bind('<FocusIn>', on_tipo_focus_in)
        self.tipo_entry.bind('<FocusOut>', on_tipo_focus_out)
        
        ttk.Label(form_frame, text="Preço (R$):", font=("Segoe UI", 10)).grid(
            row=0, column=2, sticky=W, padx=(0, 10), pady=8
        )
        ttk.Entry(form_frame, textvariable=self.preco, width=15).grid(
            row=0, column=3, sticky=W, pady=8
        )
        
        # Linha 2: Sabor e Estoque
        ttk.Label(form_frame, text="Sabor:", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky=W, padx=(0, 10), pady=8
        )
        ttk.Entry(form_frame, textvariable=self.sabor, width=32).grid(
            row=1, column=1, sticky=W, padx=(0, 20), pady=8
        )
        
        ttk.Label(form_frame, text="Estoque:", font=("Segoe UI", 10)).grid(
            row=1, column=2, sticky=W, padx=(0, 10), pady=8
        )
        ttk.Entry(form_frame, textvariable=self.estoque, width=15).grid(
            row=1, column=3, sticky=W, pady=8
        )
        
        # ========== BOTÕES ==========
        btns_frame = ttk.Frame(main_container)
        btns_frame.pack(fill=X, pady=10)
        
        ttk.Button(btns_frame, text="💾 Cadastrar", bootstyle=SUCCESS,
                  command=self.salvar_produto).pack(side=LEFT, padx=6)
        ttk.Button(btns_frame, text="✏️ Editar", bootstyle=INFO,
                  command=self.iniciar_edicao).pack(side=LEFT, padx=6)
        ttk.Button(btns_frame, text="🗑️ Excluir", bootstyle=DANGER,
                  command=self.excluir_produto).pack(side=LEFT, padx=6)
        ttk.Button(btns_frame, text="🔄 Limpar Campos", bootstyle=SECONDARY,
                  command=self._limpar_campos).pack(side=LEFT, padx=6)
        # Botão voltar
        ttk.Button(btns_frame, text="🔙 Voltar ao Menu", bootstyle=INFO,
                  command=self.voltar_dashboard).pack(side=RIGHT, padx=6)


        # ========== TABELA ==========
        table_frame = ttk.Labelframe(main_container, text="Produtos Cadastrados", padding=10)
        table_frame.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        cols = ("ID", "Tipo", "Sabor", "Preço", "Estoque")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        
        for c in cols:
            self.tree.heading(c, text=c, anchor=CENTER)
            width = 80 if c == "ID" else 150
            self.tree.column(c, anchor=CENTER, width=width)
        
        self.tree.pack(fill=BOTH, expand=True, side=LEFT)
        self.tree.bind("<ButtonRelease-1>", self._on_select)
        
        # Scrollbar
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)

    def _carregar_produtos(self):
        """Carrega produtos na tabela"""
        # Limpa tabela
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        try:
            for p in listar_produtos():
                # p: (id, tipo, sabor, preco, estoque)
                preco_fmt = f"{float(p[3]):.2f}".replace(".", ",")
                self.tree.insert("", "end", values=(p[0], p[1], p[2], preco_fmt, p[4]))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar produtos: {e}")

    def _on_select(self, event=None):
        """Preenche campos ao selecionar produto"""
        sel = self.tree.selection()
        if not sel:
            return
        
        vals = self.tree.item(sel[0])["values"]
        self.selected_id = vals[0]
        
        # Limpa placeholder
        self.tipo_entry.config(foreground='white')
        self.nome_tipo.set(vals[1])
        
        self.sabor.set(vals[2] if vals[2] else "")
        
        # Preço com vírgula → ponto
        preco_str = str(vals[3]).replace(",", ".")
        self.preco.set(preco_str)
        
        self.estoque.set(str(vals[4]))

    def salvar_produto(self):
        """Salva ou atualiza produto"""
        tipo = self.nome_tipo.get().strip()
        sabor = self.sabor.get().strip()
        preco = self.preco.get().strip().replace(",", ".")
        estoque = self.estoque.get().strip() or "0"
        
        # Validação
        if not tipo or tipo == self.tipo_placeholder:
            messagebox.showwarning("Validação", "O campo 'Tipo' é obrigatório.")
            return
        
        if not preco:
            messagebox.showwarning("Validação", "O campo 'Preço' é obrigatório.")
            return
        
        try:
            preco_val = float(preco)
            estoque_val = int(estoque)
        except ValueError:
            messagebox.showwarning("Validação", "Preço deve ser numérico e estoque inteiro.")
            return
        
        try:
            if self.selected_id:
                atualizar_produto(self.selected_id, tipo, sabor, preco_val, estoque_val)
                messagebox.showinfo("Sucesso", "Produto atualizado.")
            else:
                inserir_produto(tipo, sabor, preco_val, estoque_val)
                messagebox.showinfo("Sucesso", "Produto cadastrado.")
            
            # Notifica mudança
            self.sync.notify_change('produtos')
            print("✅ Notificação enviada: produtos atualizados")
            
            self._limpar_campos()
            self._carregar_produtos()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def iniciar_edicao(self):
        """Inicia edição de produto selecionado"""
        if not self.selected_id:
            messagebox.showwarning("Seleção", "Selecione um produto na lista para editar.")
            return
        messagebox.showinfo("Editar", "Altere os campos e clique em 'Cadastrar' para confirmar.")

    def excluir_produto(self):
        """Exclui produto selecionado"""
        if not self.selected_id:
            messagebox.showwarning("Seleção", "Selecione um produto para excluir.")
            return
        
        if messagebox.askyesno("Confirmar", "Deseja excluir o produto selecionado?"):
            try:
                excluir_produto(self.selected_id)
                
                # Notifica mudança
                self.sync.notify_change('produtos')
                print("✅ Notificação enviada: produto excluído")
                
                messagebox.showinfo("Sucesso", "Produto excluído com sucesso!")
                self._limpar_campos()
                self._carregar_produtos()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao excluir: {e}")

    def _limpar_campos(self):
        """Limpa formulário"""
        self.selected_id = None
        
        # Restaura placeholder
        self.nome_tipo.set(self.tipo_placeholder)
        self.tipo_entry.config(foreground='gray')
        
        self.sabor.set("")
        self.preco.set("")
        self.estoque.set("")

    def voltar_dashboard(self):
        """Volta para dashboard - SEM subprocess"""
        self.destroy()
        from ui.dashboard_ui import DashboardUI
        DashboardUI(master=self.master, 
                    display_name=self.display_name, 
                    role=self.role)