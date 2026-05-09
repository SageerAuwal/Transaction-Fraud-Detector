#!/bin/bash

echo "------------------------------------------------"
echo "🛡️ Gojo Sentinel - Starting Offline Server"
echo "------------------------------------------------"

# Activate environment and run
source venv/bin/activate

if [ $? -eq 0 ]; then
    python3 app.py
else
    echo "❌ ERROR: Could not activate virtual environment."
    echo "Please run: bash setup_linux.sh first."
fi

echo "------------------------------------------------"
