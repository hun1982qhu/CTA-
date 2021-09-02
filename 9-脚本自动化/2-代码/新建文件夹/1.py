#%%
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from openpyxl.utils import get_column_letter
from dataclasses import dataclass

from functools import partial

import openpyxl
import numpy as np
from pandas import DataFrame
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from vnpy.trader.constant import (Direction, Exchange, Interval, Offset)



date1 = date(2021, 1, 3)
date2 = date(2021, 1, 1)

print(date1 - date2)

if (date1 - date2) > timedelta(days=1):
    print("True")
    
dict1 = defaultdict(list)
dict1["date1"].append("a")
print(dict1["date1"])

dict2 = {1: "a", 2: "b", 3: "c"}
print(dict2.values())

list1 = [1, 2, 3, 4]
print(list1[:-1])