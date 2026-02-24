@echo off
py -m pip install PyQt5 Pillow rembg
py "%~dp0배경제거.py"
pause
