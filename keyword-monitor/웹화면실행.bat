@echo off
chcp 65001 > nul
echo 웹 화면을 시작합니다...
echo 종료하려면 이 창을 닫으세요.
echo.
start /min "" cmd /c "timeout /t 3 /nobreak > nul && start http://localhost:8501"
py -3.11 -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
pause
