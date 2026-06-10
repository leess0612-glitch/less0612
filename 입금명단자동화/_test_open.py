import win32api
import xlwings as xw
from main import EXCEL_PATH, _open_workbook

app = xw.App(visible=False)
try:
    short_path = win32api.GetShortPathName(str(EXCEL_PATH))
    wb = _open_workbook(app, short_path)
    ws = wb.sheets.active
    print("OK - sheet name:", ws.name, "| last row:", ws.used_range.last_cell.row)
    wb.close()
finally:
    app.quit()
