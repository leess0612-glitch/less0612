@echo off
py -m pip uninstall -y onnxruntime onnxruntime-gpu onnxruntime-silicon
py -m pip install PyQt5 Pillow "rembg[cpu]"
py "%~dp0bg_remove.py"
pause
