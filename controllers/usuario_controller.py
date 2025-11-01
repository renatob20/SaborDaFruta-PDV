from models.usuario_model import Usuario
#from ..models.usuario_model import Usuario


def criar_usuario(nome, cpf, celular, usuario, senha):
    try:
        novo_usuario = Usuario(nome=nome, cpf=cpf, celular=celular, username=usuario, senha=senha, role="operador")
        return novo_usuario.salvar()
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return False
