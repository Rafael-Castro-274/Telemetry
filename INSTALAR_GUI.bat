@echo off
chcp 65001 >nul
title Corredor X - Instalador Gráfico
python instalador_gui.py
if errorlevel 1 (
    echo.
    echo ❌ Erro ao executar o instalador
    echo.
    echo Verifique se o Python está instalado corretamente.
    pause
)
