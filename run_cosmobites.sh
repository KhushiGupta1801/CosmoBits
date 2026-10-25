#!/usr/bin/env bash
# ==============================================================================
# Cosmo Bites — Space Technology & Satellite Tracking Platform
# Run Script for Linux & macOS
# Launches the complete application on localhost in the browser
# ==============================================================================

set -e

# Change directory to the folder where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "============================================================"
echo "          COSMO BITES — MISSION CONTROL PLATFORM            "
echo "============================================================"
echo ""

# Find available Python 3 binary
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        # Check python version is at least 3.9
        VER=$("$cmd" -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)" 2>/dev/null || echo "0")
        if [ "$VER" -ge 39 ]; then
            PYTHON_BIN="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "[-] ERROR: Python 3 (version 3.9+) was not found."
    echo "    Please install Python 3.10, 3.11, or 3.12:"
    echo "    • Ubuntu / Debian: sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
    echo "    • Fedora / RHEL:   sudo dnf install -y python3 python3-pip"
    echo "    • Arch Linux:      sudo pacman -S python python-pip"
    echo "    • macOS:           brew install python@3.11"
    echo ""
    exit 1
fi

echo "[*] Using Python: $($PYTHON_BIN --version 2>&1)"

# Check virtual environment
VENV_DIR=".venv"
# If existing .venv is from Windows (has Scripts instead of bin), use .venv_unix
if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[!] Existing .venv was created on Windows. Initializing Unix virtual environment (.venv_unix)..."
    VENV_DIR=".venv_unix"
fi

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[1/3] Creating virtual environment ($VENV_DIR)..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "[-] Failed to create virtual environment."
        echo "    Ensure python3-venv is installed: sudo apt install python3-venv"
        exit 1
    fi
fi

# Activate environment
echo "[2/3] Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip & install requirements
echo "[*] Checking and installing dependencies from requirements.txt..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

# Open browser and run Streamlit
echo ""
echo "[3/3] Starting Cosmo Bites..."
echo "============================================================"
echo " Access dashboard in browser: http://localhost:8501         "
echo " Press Ctrl+C in this terminal to stop the server.          "
echo "============================================================"
echo ""

# Launch Streamlit server
exec python -m streamlit run app.py --server.port 8501 --server.headless false
