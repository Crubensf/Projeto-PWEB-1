@echo off
REM Windows — duplo clique para iniciar o Van Já
cd /d "%~dp0"
python start.py
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Python nao encontrado. Instale em https://python.org
    pause
)
