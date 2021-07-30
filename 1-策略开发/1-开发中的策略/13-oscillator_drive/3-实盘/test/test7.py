#%%
import openpyxl
import datetime

wb = openpyxl.Workbook()
sheet = wb.active

sheet.column_dimensions["B"].number_format = "yyyy-mm-dd hh:mm:ss:ff"

sheet["B2"] = datetime.datetime.fromisoformat('2020-12-12 12:22:22:888')

wb.save("D:/CTA/1-策略开发/1-开发中的策略/14-oscillator_drive/2-实盘/datetime.xlsx")