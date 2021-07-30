#%%
import openpyxl
from openpyxl.styles import Font

wb = openpyxl.load_workbook("D:/CTA/1-策略开发/1-开发中的策略/14-oscillator_drive/2-实盘/produceSales.xlsx")

sheet = wb.active

sheet.insert_rows(2)

wb.save("D:/CTA/1-策略开发/1-开发中的策略/14-oscillator_drive/2-实盘/produceSales.xlsx")