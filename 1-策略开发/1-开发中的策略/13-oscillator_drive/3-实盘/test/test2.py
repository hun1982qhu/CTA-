#%%
# import openpyxl
# import pprint
# from openpyxl.utils import get_column_letter, column_index_from_string
# import datetime

# print("opening workbook...")
# wb = openpyxl.load_workbook("D:/CTA/1-策略开发/1-开发中的策略/14-oscillator_drive/2-实盘/censuspopdata.xlsx")

# print(type(wb.sheetnames))

# sheet = wb["Population by Census Tract"]

# countyData = {}

# print("reading rows...")

# countyData.setdefault(state, {})
# countyData[state].setdefault(county, {"tracts": 0, "pop": 0})

# for row in range(2, sheet.max_row +1):
#     state = sheet["B"+str(row)].value
#     county = sheet["C"+str(row)].value
#     pop = sheet["D"+str(row)].value  
#     countyData[state][county]["tracts"] += 1
#     countyData[state][county]["pop"] += int(pop)

trade_record_dict = {
            "vt_symbol": 1,
            "orderid": 2,
            "tradeid": 3,
            "offset": 4,
            "direction": 5,
            "price": 6,
            "volume": 7,
            "datetime": 8,
            "strategy": 9,
            "strategy_name": 10
        }

print(list(trade_record_dict.values())[1])

for i in trade_record_dict.values():
    print(i)