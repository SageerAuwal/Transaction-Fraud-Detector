#!/bin/bash

echo "------------------------------------------------"
echo "🛡️ Gojo Sentinel - Linux/Ubuntu Setup"
echo "------------------------------------------------"

# Check for python
if ! command -v python3 &> /dev/null
then
    echo "❌ ERROR: Python3 could not be found. Please install it: sudo apt install python3 python3-venv"
    exit
fi

echo "📦 Creating Virtual Environment..."
python3 -m venv venv

echo "🚀 Installing dependencies..."
source venv/bin/bin/activate 2>/dev/null || source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "🧠 Training AI Model..."
python3 generate_data.py
python3 train.py

echo ""
echo "✅ SETUP COMPLETE!"
echo "👉 You can now run the system using: bash run_linux.sh"
echo "------------------------------------------------"
