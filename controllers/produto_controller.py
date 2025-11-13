# controllers/produto_controller.py
from models import produto_model

def inicializar_produtos():
    produto_model.criar_tabela_produtos()

def criar_produto(nome, tipo, sabor, preco):
    if not nome or not tipo or not sabor or not preco:
        raise ValueError("Todos os campos são obrigatórios.")
    try:
        preco = float(preco)
        if preco <= 0:
            raise ValueError("O preço deve ser maior que zero.")
    except ValueError:
        raise ValueError("O preço deve ser numérico e positivo.")
    produto_model.inserir_produto(nome.strip(), tipo.strip(), sabor.strip(), preco)

def listar_produtos():
    return produto_model.listar_produtos()

def atualizar_produto(id_produto, nome, tipo, sabor, preco):
    if not nome or not tipo or not sabor or not preco:
        raise ValueError("Todos os campos são obrigatórios.")
    try:
        preco = float(preco)
        if preco <= 0:
            raise ValueError("O preço deve ser maior que zero.")
    except ValueError:
        raise ValueError("O preço deve ser numérico e positivo.")
    produto_model.atualizar_produto(id_produto, nome.strip(), tipo.strip(), sabor.strip(), preco)

def excluir_produto(id_produto):
    produto_model.excluir_produto(id_produto)
