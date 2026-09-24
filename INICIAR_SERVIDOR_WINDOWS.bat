@echo off
setlocal
cd /d "%~dp0"
echo Iniciando o servidor de casos compartilhados neste computador...
echo Deixe esta janela aberta enquanto usar os recursos online.
py -m uvicorn techdiagnostico_servidor:app --host 127.0.0.1 --port 8000
if errorlevel 1 (
    echo.
    echo O servidor nao iniciou. Instale primeiro as bibliotecas seguindo as instrucoes.
    pause
)
