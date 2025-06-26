@echo off
echo 🦕 Starting BrontoBox with UTF-8 encoding...
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
chcp 65001 > nul

echo ✅ Encoding set to UTF-8
echo 🚀 Starting BrontoBox API server...

python brontobox_api.py

pause