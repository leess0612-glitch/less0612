@echo off
py -3.11 -m pip install PyQt5 Pillow "numpy<2" "onnxruntime==1.16.3"
py -3.11 "%~dp0bg_remove.py"
pause
