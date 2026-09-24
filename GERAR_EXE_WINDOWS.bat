@echo off
setlocal
cd /d "%~dp0"
echo Preparando o aplicativo...
py -m pip install pandas pyinstaller
if errorlevel 1 goto erro
echo Criando o executavel para este Windows...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name TechDiagnostico techdiagnostico_interface.py
if errorlevel 1 goto erro
echo.
echo Pronto! Abra dist\TechDiagnostico.exe com duplo clique.
pause
exit /b 0
:erro
echo.
echo Falha ao gerar o executavel. Confira a mensagem acima e tente a opcao pelo terminal.
pause
exit /b 1
