@echo off
cd /d "%~dp0"
if not exist .venv (
    echo A instalar pela primeira vez, aguarde...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\streamlit run app.py
