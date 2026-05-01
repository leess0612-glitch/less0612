@echo off
cd /d "C:\Users\a\Desktop\안티그라비티"
git add -A
git diff --cached --quiet && exit /b 0
for /f "tokens=*" %%i in ('powershell -command "Get-Date -Format 'yyyy. M. d. tt hh:mm:ss'"') do set DATETIME=%%i
git commit -m "auto: %DATETIME%"
git push origin main
