@echo off
py -3.11 -m pip install PyQt5 Pillow onnxruntime numpy
py -3.11 "%~dp0bg_remove.py"
pause
