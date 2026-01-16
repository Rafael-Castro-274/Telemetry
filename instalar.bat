@echo off
chcp 65001 >nul
echo ========================================
echo    Corredor X - Instalação
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale o Python 3.7 ou superior:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version
echo.

REM Verifica se pip está disponível
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip não encontrado!
    echo.
    pause
    exit /b 1
)

echo ✅ pip encontrado
echo.

REM Pergunta sobre ambiente virtual
echo Deseja criar um ambiente virtual? (Recomendado)
echo [S] Sim    [N] Não
echo.
choice /C SN /N /M "Escolha uma opção: "

if errorlevel 2 goto :install_deps
if errorlevel 1 goto :create_venv

:create_venv
echo.
echo 📦 Criando ambiente virtual...
python -m venv venv
if errorlevel 1 (
    echo ❌ Erro ao criar ambiente virtual
    pause
    exit /b 1
)

echo ✅ Ambiente virtual criado
echo.
echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate.bat

:install_deps
echo.
echo 📥 Instalando dependências...
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)

echo.
echo ========================================
echo    ✅ Instalação concluída com sucesso!
echo ========================================
echo.
echo Para executar o projeto:
echo   - Use: executar.bat
echo   - Ou: python corredorx.py
echo.
pause
