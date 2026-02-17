#!/bin/bash

# Ensure Homebrew is in PATH
eval "$(/opt/homebrew/bin/brew shellenv)"

echo "Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3 via Homebrew..."
    brew install python
else
    # Check if python3 is system python (which is bad for tkinter)
    PY_PATH=$(which python3)
    if [[ "$PY_PATH" == "/usr/bin/python3" ]]; then
        echo "System Python detected. Installing Homebrew Python for better Tkinter support..."
        brew install python
        brew link --overwrite python
    fi
fi

echo "Installing python-tk (required for GUI)..."
brew install python-tk

echo "Setting up Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Running Application..."
python3 main.py
