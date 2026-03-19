@echo off
title OpenEMR RAG - Setup
echo.
echo ========================================
echo  OpenEMR Clinical Decision Support System
echo  Setup Script
echo ========================================
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)
echo OK: Python installed

echo.
echo [2/4] Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)
echo OK: Packages installed

echo.
echo [3/4] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama not found. Install from https://ollama.ai
    echo Run: ollama pull alibayram/medgemma:4b
    echo Run: ollama pull nomic-embed-text
) else (
    echo OK: Ollama installed
    echo.
    echo Pulling required models (first time only)...
    ollama pull alibayram/medgemma:4b
    ollama pull nomic-embed-text
)

echo.
echo [4/4] Verifying setup...
python -c "from openemr_rag import OpenEMRRAG; print('OK: Module imports successfully')"

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To run the application:
echo   python openemr_rag.py
echo.
echo Or use the launcher:
echo   Run-RAG-Interactive.bat
echo.
pause
