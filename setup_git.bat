@echo off
echo Criando arquivo .gitignore...

(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo .pytest_cache/
echo .coverage
echo .env
echo venv/
echo 
echo # VSCode
echo .vscode/
echo .vs/
echo 
echo # Database
echo *.db
echo *.sqlite3
echo 
echo # Sistema
echo .DS_Store
echo Thumbs.db
) > .gitignore

echo Arquivo .gitignore criado com sucesso!
echo Inicializando repositório Git...

git init
git add .
git status

echo.
echo Setup concluído! Para continuar:
echo 1. Verifique os arquivos com 'git status'
echo 2. Faça o commit inicial com: git commit -m "Commit inicial"
echo 3. Configure o repositório remoto e faça push

pause