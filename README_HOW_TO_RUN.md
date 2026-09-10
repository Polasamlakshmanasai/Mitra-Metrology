# Mitra Metrology - How to Run

## The Error You Got

ModuleNotFoundError: No module named 'app'

WHY: You are either running from the WRONG folder, or using the WRONG Python.
The 'app' package lives at backend/app/. Python only finds it when the working
directory is 'backend/'.

---

## CORRECT WAY 1: One-Click Script

Open PowerShell in the project root:

    .\start-dev.ps1

This opens two windows:
  - Backend  -> http://localhost:8000
  - Frontend -> http://localhost:5173

---

## CORRECT WAY 2: Manual (Two Terminals)

### Terminal 1 - Backend (MUST cd into backend/)

    cd backend
    ..\backend\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

### Terminal 2 - Frontend

    cd frontend
    npm run dev

---

## WRONG WAYS (These cause the error)

    # WRONG - running from root
    python -m uvicorn app.main:app --port 8000

    # WRONG - running the file directly
    python backend/app/main.py

    # WRONG - using system python instead of venv
    python -m uvicorn backend.app.main:app --port 8000

---

## URLs Once Running

  Frontend:        http://localhost:5173
  Backend API:     http://localhost:8000
  Swagger/Docs:    http://localhost:8000/docs

---

## Test Login Credentials

  Citizen  -> user@mitra.com           / User@123
  Officer  -> officer_22472@mitra.gov.in / Officer@123

---

## Quick Troubleshooting

  Error: No module named 'app'
  Fix:   cd into backend/ before running uvicorn

  Error: No module named 'cv2'
  Fix:   backend\venv\Scripts\pip install opencv-python

  Error: No module named 'fastapi'
  Fix:   backend\venv\Scripts\pip install -r backend\requirements.txt

  Port 8000 in use:
  Fix:   Stop-Process -Name python -Force

  OCR returns demo data (Tesseract not installed):
  Fix:   Download from https://github.com/UB-Mannheim/tesseract/wiki
