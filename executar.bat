@echo off
chcp 65001 >nul
echo ========================================
echo    🚗 Corredor X - Telemetria ACC
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Execute primeiro: instalar.bat
    echo.
    pause
    exit /b 1
)

REM Verifica se existe ambiente virtual
if exist "venv\Scripts\activate.bat" (
    echo 🔄 Ativando ambiente virtual...
    call venv\Scripts\activate.bat
)

echo.
echo ========================================
echo    Instruções:
echo ========================================
echo.
echo 1. Certifique-se de que o ACC está rodando
echo 2. Entre em uma sessão (treino/corrida)
echo 3. A janela de telemetria abrirá automaticamente
echo 4. Pressione Ctrl+C para finalizar e gerar PDF
echo.
echo ========================================
echo.
pause

echo Iniciando telemetria...
echo.
python corredorx.py

if errorlevel 1 (
    echo.
    echo ❌ Erro ao executar o script
    echo.
    echo Possíveis causas:
    echo - ACC não está rodando
    echo - Dependências não instaladas (execute instalar.bat)
    echo.
)

pause
