from PySide6.QtWidgets import QApplication
from views.sales_view import TelaVendas
import sys

def iniciar_pdv(operador, tipo):
    app = QApplication(sys.argv)
    window = TelaVendas(operador=operador, tipo=tipo)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    # Ao chamar pelo subprocess, o nome e o tipo virão como argumentos
    if len(sys.argv) >= 3:
        operador = sys.argv[1]
        tipo = sys.argv[2]
        iniciar_pdv(operador, tipo)
    else:
        print("Erro: argumentos de usuário não recebidos.")
