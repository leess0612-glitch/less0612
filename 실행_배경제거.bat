@echo off
py -m pip install PyQt5 Pillow onnxruntime "rembg[cpu]"
py "%~dp0bg_remove.py"
pause
