# ui/produtos_ui.py
import os
import sys
import subprocess

# Garante que a raiz do projeto esteja no sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ============ ADICIONAR ESTA LINHA ============
from utils.data_sync import SimpleFlagSync
# ==============================================


import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, DoubleVar, IntVar

from models.produto_model import (
    criar_tabela_produtos,
    inserir_produto,
    listar_produtos,
    atualizar_produto,
    excluir_produto
)


class ProdutosUI(ttk.Window):
    def __init__(self, display_name="Admin", role="admin"):
        super().__init__(themename="superhero")
        
        # ---- Maximiza a Janela (Comportamento padrão para Windows) ----
        try:
            self.state("zoomed")
        except Exception:
            # Fallback para sistemas Windows onde 'zoomed' não está disponível
            # ou em casos muito específicos.
            self.attributes("-zoomed", True)
        
        self.title("📦 Cadastro de Produtos - Açaiteria")
        self.geometry("820x540")

        # inicializa tabela no banco (se necessário)
        criar_tabela_produtos()

        # ============ ADICIONAR ESTA LINHA ============
        self.sync = SimpleFlagSync()
        # ==============================================

        # variáveis
        self.display_name = display_name
        self.role = role
        self.selected_id = None
        self.nome_tipo = StringVar()
        self.sabor = StringVar()
        self.preco = StringVar()   # usaremos string para validação
        self.estoque = StringVar()

        self._build_ui()
        self._carregar_produtos()

    def _build_ui(self):
        # ========== HEADER COM BOTÃO VOLTAR NO TOPO ==========
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=X)
        
        ttk.Label(header_frame, text="Gerenciamento de Produtos", font=("Segoe UI", 14, "bold")).pack(side=LEFT)
        
        ttk.Button(header_frame, text="🔙 Voltar ao Menu", bootstyle="info", width=20, 
                   command=self.voltar_dashboard).pack(side=RIGHT, padx=5)
        # ======================================================

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=X, padx=12)

        # ========== CAMPO TIPO COM PLACEHOLDER INTERNO ==========
        ttk.Label(frm, text="Tipo:").grid(row=0, column=0, sticky=W, padx=6, pady=6)
        self.tipo_entry = ttk.Entry(frm, textvariable=self.nome_tipo, width=32)
        self.tipo_entry.grid(row=0, column=1, sticky=W, padx=6)
        
        # Placeholder com bind para remover ao focar
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
        # ========================================================

        ttk.Label(frm, text="Sabor:").grid(row=1, column=0, sticky=W, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.sabor, width=32).grid(row=1, column=1, sticky=W, padx=6, pady=6)

        ttk.Label(frm, text="Preço (R$):").grid(row=0, column=2, sticky=W, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.preco, width=12).grid(row=0, column=3, sticky=W)

        ttk.Label(frm, text="Estoque:").grid(row=1, column=2, sticky=W, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.estoque, width=12).grid(row=1, column=3, sticky=W)

        btns = ttk.Frame(self)
        btns.pack(fill=X, pady=8, padx=12)
        ttk.Button(btns, text="💾 Cadastrar", bootstyle=SUCCESS, command=self.salvar_produto).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="✏️ Editar", bootstyle=INFO, command=self.iniciar_edicao).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="🗑️ Excluir", bootstyle=DANGER, command=self.excluir_produto).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="🔄 Limpar Campos", bootstyle=SECONDARY, command=self._limpar_campos).pack(side=LEFT, padx=6)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill=BOTH, expand=True, padx=12, pady=8)

        cols = ("ID", "Tipo", "Sabor", "Preço", "Estoque")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor=CENTER, width=120 if c == "ID" else 160)
        self.tree.pack(fill=BOTH, expand=True, side=LEFT)

        self.tree.bind("<ButtonRelease-1>", self._on_select)

        # scrollbar
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)

    def _carregar_produtos(self):
        # limpa tabela
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
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])["values"]
        self.selected_id = vals[0]
        
        # Limpa o placeholder antes de preencher
        self.tipo_entry.config(foreground='white')
        self.nome_tipo.set(vals[1])
        
        self.sabor.set(vals[2] if vals[2] else "")  # Trata None/vazio
        # preço no tree vem com vírgula, converte para ponto
        preco_str = str(vals[3]).replace(",", ".")
        self.preco.set(preco_str)
        self.estoque.set(str(vals[4]))

    def salvar_produto(self):
        tipo = self.nome_tipo.get().strip()
        sabor = self.sabor.get().strip()
        preco = self.preco.get().strip().replace(",", ".")
        estoque = self.estoque.get().strip() or "0"

        # ========== VALIDAÇÃO MELHORADA COM PLACEHOLDER ==========
        # Verifica se o tipo é o placeholder ou está vazio
        if not tipo or tipo == self.tipo_placeholder:
            messagebox.showwarning("Validação", "O campo 'Tipo' é obrigatório.")
            return
        
        if not preco:
            messagebox.showwarning("Validação", "O campo 'Preço' é obrigatório.")
            return
        
        # Sabor pode ser vazio (opcional)
        # =========================================================

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

            # ============ NOTIFICAÇÃO DE MUDANÇA ============
            self.sync.notify_change('produtos')
            print("✅ Notificação enviada: produtos atualizados")
            # ================================================

            self._limpar_campos()
            self._carregar_produtos()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def iniciar_edicao(self):
        if not self.selected_id:
            messagebox.showwarning("Seleção", "Selecione um produto na lista para editar.")
            return
        messagebox.showinfo("Editar", "Altere os campos e clique em 'Cadastrar' para confirmar a edição.")

    def excluir_produto(self):
        if not self.selected_id:
            messagebox.showwarning("Seleção", "Selecione um produto para excluir.")
            return
        if messagebox.askyesno("Confirmar", "Deseja excluir o produto selecionado?"):
            try:
                excluir_produto(self.selected_id)
                
                # ===== NOTIFICAÇÃO DE MUDANÇA =====
                self.sync.notify_change('produtos')
                print("✅ Notificação enviada: produto excluído")
                # ==================================
                
                messagebox.showinfo("Sucesso", "Produto excluído com sucesso!")
                self._limpar_campos()
                self._carregar_produtos()

            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao excluir: {e}")

    def _limpar_campos(self):
        self.selected_id = None
        
        # Restaura o placeholder no campo tipo
        self.nome_tipo.set(self.tipo_placeholder)
        self.tipo_entry.config(foreground='gray')
        
        self.sabor.set("")
        self.preco.set("")
        self.estoque.set("")

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


if __name__ == "__main__":
    app = ProdutosUI("Admin", "admin")
    app.mainloop()