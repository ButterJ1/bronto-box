# run_brontobox.bat
# Windows batch script to run BrontoBox with UTF-8 encoding

@echo off
echo 🦕 Starting BrontoBox with UTF-8 encoding...

# Set UTF-8 encoding for Python
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

# Change console code page to UTF-8
chcp 65001 > nul

echo ✅ Encoding set to UTF-8
echo 🚀 Starting BrontoBox API server...

# Run the Python backend
python brontobox_api.py

pause