@echo off
echo Python 3.11 installing...
py install 3.11
echo.
echo Installing packages...
py -3.11 -m pip install PyQt5 Pillow "rembg[cpu]"
echo.
echo Starting app...
py -3.11 "%~dp0bg_remove.py"
pause
