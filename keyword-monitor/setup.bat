@echo off
chcp 65001 > nul
echo =============================================
echo   당현함 키워드 모니터링 - 초기 설치
echo =============================================
echo.

py -3.11 -m pip install -r requirements.txt
if errorlevel 1 (
    echo [오류] pip install 실패. Python 3.11이 설치되어 있는지 확인하세요.
    pause
    exit /b 1
)

py -3.11 -m playwright install chromium
if errorlevel 1 (
    echo [오류] playwright 설치 실패.
    pause
    exit /b 1
)

echo.
echo =============================================
echo   설치 완료!
echo   실행: python main.py
echo =============================================
pause
