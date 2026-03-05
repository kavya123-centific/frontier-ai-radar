#!/bin/bash
set -e

echo ""
echo "===================================================="
echo "  Frontier AI Radar - Mac/Linux Quick Setup"
echo "===================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found."
    echo "Install from https://python.org/downloads or run: brew install python3"
    exit 1
fi

echo "[1/3] Installing dependencies..."
pip3 install -r backend/requirements.txt

echo ""
echo "[2/3] Checking .env file..."
if [ ! -f backend/.env ]; then
    echo "Creating .env from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "ACTION REQUIRED: Open backend/.env and add your LLM_API_KEY"
    echo "Get a free key at: https://openrouter.ai"
    echo ""
    echo "Opening .env in default editor..."
    ${EDITOR:-nano} backend/.env
fi

echo ""
echo "[3/3] Starting Frontier AI Radar..."
echo ""
echo "  Dashboard: http://localhost:8501"
echo "  API Docs:  http://localhost:8000/docs"
echo "  DB Explorer: http://localhost:8000/admin/db"
echo ""
echo "Press Ctrl+C to stop."
echo ""
python3 start.py
