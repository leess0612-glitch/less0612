@echo off
py -3.11 -m pip install PyQt5 Pillow numpy "onnxruntime==1.17.3"
py -3.11 "%~dp0bg_remove.py"
pause
