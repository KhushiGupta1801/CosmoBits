#!/usr/bin/env bash
# ==============================================================================
# Cosmo Bites — 1-Click macOS Double-Click Launcher
# ==============================================================================

cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "          COSMO BITES — MISSION CONTROL (macOS)             "
echo "============================================================"
echo ""

# 1. If local virtual environment already exists and has streamlit, launch immediately
if [ -f ".venv/bin/streamlit" ]; then
    echo "[✓] Virtual environment ready. Starting Cosmo Bites..."
    echo "[*] Opening http://localhost:8501 in your browser..."
    (sleep 1 && open "http://localhost:8501") &
    exec ".venv/bin/python" -m streamlit run app.py --server.port 8501 --server.headless false
elif [ -f ".venv_unix/bin/streamlit" ]; then
    echo "[✓] Virtual environment (.venv_unix) ready. Starting Cosmo Bites..."
    echo "[*] Opening http://localhost:8501 in your browser..."
    (sleep 1 && open "http://localhost:8501") &
    exec ".venv_unix/bin/python" -m streamlit run app.py --server.port 8501 --server.headless false
elif [ -f "../Cosmo_Bites/.venv/bin/streamlit" ]; then
    echo "[✓] Shared virtual environment ready. Starting Cosmo Bites..."
    echo "[*] Opening http://localhost:8501 in your browser..."
    (sleep 1 && open "http://localhost:8501") &
    exec "../Cosmo_Bites/.venv/bin/python" -m streamlit run app.py --server.port 8501 --server.headless false
else
    # 2. Otherwise run full setup script
    chmod +x ./run_cosmobites.sh
    exec ./run_cosmobites.sh
fi
