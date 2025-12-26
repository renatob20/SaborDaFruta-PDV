# controllers/usuario_controller.py
from models.user_model import create_user, listar_usuarios, get_user_by_id, update_user, delete_user

def cadastrar_usuario(nome, cpf, celular, username, password, role="operador"):
    # validações simples
    if not nome or not cpf or not username or not password:
        raise ValueError("Preencha todos os campos obrigatórios: Nome, CPF, Usuário e Senha.")
    # CPF simples: remove pontos/traços, mínimo 11 chars
    cpf_clean = ''.join(ch for ch in cpf if ch.isdigit())
    if len(cpf_clean) < 11:
        raise ValueError("CPF inválido (mínimo 11 dígitos).")

    # tenta criar e repassa exceções de integridade
    return create_user(nome, cpf_clean, celular, username, password, role, display_name=nome)


def listar_todos_usuarios():
    return listar_usuarios()


def obter_usuario(user_id):
    return get_user_by_id(user_id)


def editar_usuario(user_id, nome, cpf, celular, username, role, senha=None):
    cpf_clean = ''.join(ch for ch in cpf if ch.isdigit())
    if len(cpf_clean) < 11:
        raise ValueError("CPF inválido (mínimo 11 dígitos).")
    return update_user(user_id, nome, cpf_clean, celular, username, role, display_name=nome, password=senha)


def remover_usuario(user_id):
    return delete_user(user_id)
