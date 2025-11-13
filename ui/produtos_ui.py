import sys
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from tkinter import StringVar, DoubleVar, IntVar

# Ajusta o caminho para importar o model corretamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.produto_model import ProdutoModel


class ProdutosUI(ttk.Window):
    def __init__(self, display_name, role):
        super().__init__(themename="superhero")
        self.title("📦 Cadastro de Produtos - Açaiteria o Sabor da Fruta")
        self.geometry("750x500")

        self.display_name = display_name
        self.role = role

        self.model = ProdutoModel()

        # Variáveis de entrada
        
        self.tipo_var = StringVar()
        self.preco_var = DoubleVar()
        self.estoque_var = IntVar()

        # Seleção da tabela
        self.selected_id = None

        self._build_ui()
        self._carregar_produtos()

    def _build_ui(self):
        ttk.Label(
            self,
            text="📦 Gerenciamento de Produtos",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        form_frame = ttk.Frame(self, padding=10)
        form_frame.pack(fill=X, pady=10)

        # Campos do formulário
        
        ttk.Label(form_frame, text="Tipo:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        ttk.Combobox(form_frame, textvariable=self.tipo_var,
                     values=["Picolé", "Sorvete"], state="readonly", width=27).grid(row=1, column=1, pady=5)

        ttk.Label(form_frame, text="Preço (R$):").grid(row=0, column=2, sticky=W, padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.preco_var, width=10).grid(row=0, column=3, pady=5)

        ttk.Label(form_frame, text="Estoque:").grid(row=1, column=2, sticky=W, padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.estoque_var, width=10).grid(row=1, column=3, pady=5)

        # Botões de ação
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="💾 Salvar", bootstyle=SUCCESS, command=self.salvar_produto).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="✏️ Editar", bootstyle=INFO, command=self.editar_produto).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="🗑️ Excluir", bootstyle=DANGER, command=self.excluir_produto).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="↩️ Voltar", bootstyle=SECONDARY, command=self.voltar_dashboard).grid(row=0, column=3, padx=5)

        # Tabela de produtos
        self.tree = ttk.Treeview(self, columns=("ID", "Tipo", "Preço", "Estoque"), show="headings", height=12)
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        for col in ("ID", "Tipo", "Preço", "Estoque"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=CENTER)

        self.tree.bind("<ButtonRelease-1>", self._selecionar_item)

    # ====== FUNÇÕES ======

    def _carregar_produtos(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        produtos = self.model.listar_produtos()
        for p in produtos:
            self.tree.insert("", "end", values=p)

    def _selecionar_item(self, event):
        item = self.tree.focus()
        if item:
            valores = self.tree.item(item, "values")
            self.selected_id = valores[0]
            self.tipo_var.set(valores[2])
            self.preco_var.set(valores[3])
            self.estoque_var.set(valores[4])

    def salvar_produto(self):
        tipo = self.tipo_var.get().strip()
        preco = self.preco_var.get()
        estoque = self.estoque_var.get()

        if self.selected_id:
            self.model.atualizar_produto(self.selected_id, tipo, preco, estoque)
            messagebox.showinfo("Atualizado", "Produto atualizado com sucesso!")
        else:
            self.model.inserir_produto(tipo, preco, estoque)
            messagebox.showinfo("Cadastrado", "Produto adicionado com sucesso!")

        self._limpar_campos()
        self._carregar_produtos()

    def editar_produto(self):
        if not self.selected_id:
            messagebox.showwarning("Seleção", "Selecione um produto para editar.")
            return
        messagebox.showinfo("Edição", "Edite os campos e clique em 'Salvar' para confirmar.")

    def excluir_produto(self):
        if not self.selected_id:
            messagebox.showwarning("Seleção", "Selecione um produto para excluir.")
            return
        confirm = messagebox.askyesno("Confirmação", "Deseja realmente excluir este produto?")
        if confirm:
            self.model.excluir_produto(self.selected_id)
            self._carregar_produtos()
            self._limpar_campos()
            messagebox.showinfo("Excluído", "Produto removido com sucesso!")

    def _limpar_campos(self):
        
        self.tipo_var.set("")
        self.preco_var.set(0.0)
        self.estoque_var.set(0)
        self.selected_id = None

    def voltar_dashboard(self):
        self.destroy()
        os.system(f"{sys.executable} ui/dashboard_ui.py {self.display_name} {self.role}")


if __name__ == "__main__":
    app = ProdutosUI("Admin", "admin")
    app.mainloop()
