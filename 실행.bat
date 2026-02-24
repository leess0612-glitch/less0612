@echo off
chcp 65001 >nul
echo 패키지 확인 중...
pip install -q PyQt5 Pillow
echo.
echo 이미지 합성기 시작...
python 합성기.py
pause
