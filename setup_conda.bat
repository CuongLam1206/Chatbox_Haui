@echo off
REM Conda Environment Setup Script for Agentic RAG Chatbot

echo ============================================================
echo CREATING CONDA ENVIRONMENT: agentic_rag
echo ============================================================

REM Create conda environment
echo.
echo [1/3] Creating conda environment with Python 3.11...
call conda create -n agentic_rag python=3.11 -y

if errorlevel 1 (
    echo Error: Failed to create conda environment
    pause
    exit /b 1
)

echo.
echo [2/3] Activating environment...
call conda activate agentic_rag

if errorlevel 1 (
    echo Error: Failed to activate environment
    pause
    exit /b 1
)

echo.
echo [3/3] Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS! Environment 'agentic_rag' is ready
echo ============================================================
echo.
echo Next steps:
echo 1. Create .env file with your OPENAI_API_KEY
echo 2. Copy documents to data/documents/
echo 3. Run: conda activate agentic_rag
echo 4. Run: python initialize.py
echo 5. Run: python demo.py
echo.
pause
