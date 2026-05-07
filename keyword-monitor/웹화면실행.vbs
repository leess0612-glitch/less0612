Set oShell = CreateObject("WScript.Shell")
oShell.Run "py -3.11 -m streamlit run app.py --server.headless true --browser.gatherUsageStats false", 0, False
WScript.Sleep 3000
oShell.Run "http://localhost:8501"
