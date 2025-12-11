
🍧 SaborDaFruta-PDV

Sistema de Ponto de Venda (PDV) para Açaiteria e Sorveteria

Um sistema desktop completo desenvolvido em Python, utilizando Tkinter + ttkbootstrap, ideal para pequenos negócios como açaiterias, sorveterias e lanchonetes.
Permite controle total de vendas, estoque, produtos, usuários, ponto e relatórios.

📂 Estrutura do Projeto
SaborDaFruta-PDV/
├── ui/                    # Telas e janelas do sistema
├── database/              # Banco de dados SQLite e migrations automáticas
├── utils/                 # Funções auxiliares
├── main.py                # Ponto de entrada do sistema
└── README.md              # Documentação

🖥️ Funcionalidades
🔐 Login

Autenticação por usuário e senha

Perfis: Admin e Operador

🧭 Dashboard

Centraliza toda a navegação do sistema:

🛒 Vendas

📦 Produtos

📦 Estoque

👤 Usuários

⏰ Bater Ponto

📊 Relatórios

🚪 Logout

🛒 Vendas

Seleção dinâmica de tipo e produto

Suporte a vendas por quantidade e peso (kg)

Carrinho estilo cupom fiscal

Cálculo automático de:

Total

Troco

Valor recebido

Registro da venda no banco

Registro dos itens da venda

Atualização automática de estoque

📦 Produtos

Cadastro completo de produtos:

Nome

Tipo

Sabor

Preço

Estoque

Produtos cadastrados aparecem automaticamente na tela de Vendas.

🧊 Estoque

Gerencia movimentações:

Entrada e saída

Histórico detalhado

Atualização automática após vendas

Aviso de estoque baixo

👤 Usuários

Cadastro de colaboradores

Permissões por perfil (admin/operador)

⏰ Controle de Ponto

Registro de batidas:

Entrada 1

Saída 1

Entrada 2

Saída 2

Histórico por período

📊 Relatórios

Relatórios de vendas e pontos

Filtragem por período

Base para exportação (CSV/Excel/PDF)

🗄️ Banco de Dados

Utiliza SQLite, armazenando tudo em:

database/acaiteria.db

Tabelas principais:

usuarios

produtos

vendas

venda_items

estoque_movimentos

ponto_batidas

Migrations automáticos garantem que nenhuma atualização cause perda de dados.

🚀 Como Executar
1. Instale as dependências
pip install ttkbootstrap

2. Execute o sistema
python main.py

🧱 Como as Telas se Relacionam
Tela	Ação
Login	→ Dashboard
Dashboard	→ Vendas / Produtos / Estoque / Ponto / Relatórios
Produtos	Atualiza Vendas + Estoque
Estoque	Atualiza Vendas automaticamente
Vendas	Gera registro de venda + altera estoque
Relatórios	Consulta todas as tabelas

Fluxo principal:
Produtos → Estoque → Vendas → Relatórios

📦 Gerar o Executável (.exe)

O sistema pode ser distribuído como programa de instalação.

Instale o PyInstaller
pip install pyinstaller

Gere o executável
pyinstaller --noconfirm --clean --windowed --name "SaborDaFruta-PDV" main.py


O arquivo final aparecerá em:

dist/SaborDaFruta-PDV.exe


⚠️ Não esqueça de incluir a pasta database/ junto ao executável para preservar dados.

📈 Evolução do Sistema (Roadmap)

Aqui estão os próximos passos sugeridos para evolução do PDV.

📌 1 — Relatórios Avançados (períodos longos até 1 ano)
Objetivo:

Permitir filtros como:

Últimos 7 dias

Últimos 30 dias

Últimos 3 meses

Últimos 6 meses

Último 1 ano

Período personalizado

O que fazer:

Criar consultas SQL filtrando por data:

SELECT * FROM vendas
WHERE data_venda BETWEEN ? AND ?
ORDER BY data_venda DESC;


Criar componentes no relatório:

DateEntry inicial

DateEntry final

Botões rápidos (7d, 30d, 1 ano)

Exibir:

Número de vendas

Ticket médio

Total em dinheiro, crédito, débito, Pix

Gráfico (opcional) com matplotlib

📌 2 — Exportação de Dados
Exportar para:
✔ CSV

Simples e rápido:

import csv

with open("relatorio.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Data", "Total"])
    writer.writerows(vendas_list)

✔ Excel (.xlsx)

Usando openpyxl:

pip install openpyxl

from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["ID", "Data", "Total"])
for linha in vendas:
    ws.append(linha)
wb.save("relatorio.xlsx")

✔ PDF

Usando reportlab:

pip install reportlab


Gerar recibo, relatórios e até cupom não fiscal.

📌 3 — Atualizador / Instalação sem perder dados
Cenário:

Instalar nova versão sem perder o banco.

Procedimento recomendado:

Gerar o instalador com PyInstaller

Garantir que acaiteria.db NÃO seja recriado

Criar sistema de migrations automáticas como já existe

Gerar instalador com pastas separadas:

/app
/database   ← preservado


No instalador, não sobrescrever database/.

📌 4 — Recursos futuros sugeridos

✔ Cupom impresso em impressora térmica
✔ Painel administrativo com gráficos
✔ Backup automático diário
✔ Sincronização em nuvem (opcional)
✔ Multi-caixa / multi-terminal
