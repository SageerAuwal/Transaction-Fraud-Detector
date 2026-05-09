# 🛡️ Gojo Sentinel — Offline User Guide

Follow these steps to run the Gojo Sentinel Fraud Detection system on any Windows computer.

## 1. Prerequisites
You must have **Python 3.10 or higher** installed. 
- Download it from [python.org](https://www.python.org/downloads/).
- **Important**: During installation, check the box that says **"Add Python to PATH"**.

## 2. One-Time Setup
Once you have the project folder on the new computer:
1.  Find the file **`setup_offline.bat`** and **double-click** it.
2.  Wait for the black window to finish (it will install the AI libraries).
3.  When it says "SETUP COMPLETE", you can close the window.

## 3. Running the System
Whenever you want to use the model:
1.  **Double-click** **`run_offline.bat`**.
2.  Keep the terminal window open.
3.  Open your browser (Chrome or Edge) and go to:
    👉 **`http://localhost:8000`**

## 4. Troubleshooting
- **Port Error**: If it says "Port 8000 is in use", close any other apps that might be using it.
- **Python Error**: If it says "Python not found", ensure Python is installed and added to your system PATH.

## 5. Linux / Ubuntu Instructions
If you are using Ubuntu or Linux:
1.  Open the terminal in the project folder.
2.  Run the setup: **`bash setup_linux.sh`**
3.  Start the server: **`bash run_linux.sh`**
4.  Open **`http://localhost:8000`** in your browser.

---
*Gojo Sentinel — Nigerian Fintech Security*
