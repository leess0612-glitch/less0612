@echo off
chcp 65001 > nul
echo 웹 화면을 시작합니다...
echo 브라우저에서 http://localhost:8501 로 접속하세요.
echo 종료하려면 이 창을 닫으세요.
echo.
py -3.11 -m streamlit run app.py --server.headless true
pause
