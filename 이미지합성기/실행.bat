@echo off
py -m pip install PyQt5 Pillow
py "%~dp0app.py"
pause
