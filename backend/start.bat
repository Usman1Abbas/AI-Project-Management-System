@echo off

if not exist .env (
    echo Warning: .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please edit .env with your API keys before running again.
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Starting FastAPI server...
python main.py

