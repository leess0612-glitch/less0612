@echo off
py -m pip install PyQt5 Pillow rembg
py "%~dp0bg_remove.py"
pause
