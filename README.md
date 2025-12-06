Master
o que está funcionando:

 - Dasboard novo layout  - OK
 
 - Tela Bater Ponto - OK

 - Tela Produtos:   - OK


Comecarei a atuar nessa tela com a branch de feature/vendas
 - Tela de vendas:
     
     1 - OK
     Vendas abre normalmente, corrigido  -->> OK
     - ao clicar apresenta o erro: Não foi possivel abrir vendas: cannot acesses local variable 'VendasUI' where it is not associated with a value (OK, abre o novo layout)
     
     
     2 - OK
     - Ao registar uma venda apresenta a mensagem: Falha ao gravar vendas:
     NOT NULL constraint failed: vendas.tipo_produto
         --->>  OK
     
     3 - OK
     - Ao adicionar sorvete e informar o valor de 100 no campo Peso KG o subtotal passa para 5.500,00
         ---> OK


    4  - OK
    Trabalhando nesse erro
     - Botão sair: fecha o programa e apresenta o erro no terminal: A sintaxe do nome do arquivo, do nome do diretório ou do rótulo do volume está incorreta.
  
   5  - realizar ajuste
   - Tela de Usuários:>
        - Alinhar os itens cadastrados na tabela, centralizar as informaçoes de cada coluna

  
  6   --  em ajuste
  - Relatórios:
    - Abre a tela Nova com a mensagem de erro: Não foi possível abrir Relatórios: settings ',' as master creates a transient/master cycle
    - Ao clicar em voltar, apresenta o erro
    Traceback (most recent call last):
  File "C:\Users\renat\AppData\Local\Programs\Python\Python312\Lib\tkinter\__init__.py", line 1968, in __call__
    return self.func(*args)
           ^^^^^^^^^^^^^^^^
  File "C:\Users\renat\OneDrive\Documentos\Acaiteria O sabor da fruta\SaborDaFruta-PDV\ui\relatorios_ui.py", line 194, in voltar_dashboard
    os.system(f'"{sys.executable}" "{dashboard_script}" {self.display_name} {self.role}')
                                                        ^^^^^^^^^^^^^^^^^
  File "C:\Users\renat\AppData\Local\Programs\Python\Python312\Lib\tkinter\__init__.py", line 2433, in __getattr__
    return getattr(self.tk, attr)
           ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: '_tkinter.tkapp' object has no attribute 'display_name'
   
- Estoque:
  - Abre a tela antiga com a emnsagem de erro: Não foi possível abrir o modulo de Estoque: sttings ',' as master creates a transient/master cycle
  - Na tela de histórico de movimentações, retirar a hora da coluna data

