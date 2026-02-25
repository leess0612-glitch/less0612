@echo off
py -3.11 -m pip install PyQt5 Pillow opencv-python numpy
py -3.11 "%~dp0bg_remove.py"
pause
