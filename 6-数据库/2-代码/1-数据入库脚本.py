from vnpy.trader.constant import (Exchange, Interval)
import pandas as pd
from vnpy.trader.database import database_manager
from vnpy.trader.object import (BarData,TickData)

# 封装函数
def move_df_to_mongodb(imported_data:pd.DataFrame,collection_name:str):
    bars = []
    start = None
    count = 0

    for row in imported_data.itertuples():

        bar = BarData(

              symbol=row.symbol,
              exchange=row.exchange,
              datetime=row.datetime,
              interval=row.interval,
              volume=row.volume,
              open_price=row.open,
              high_price=row.high,
              low_price=row.low,
              close_price=row.close,
              open_interest=row.open_interest,
              gateway_name="DB",

        )


        bars.append(bar)

        # do some statistics
        count += 1
        if not start:
            start = bar.datetime
    end = bar.datetime

    # insert into database
    database_manager.save_bar_data(bars, collection_name)
    print(f'Insert Bar: {count} from {start} - {end}')


if __name__ == "__main__":

    # 读取需要入库的csv文件，该文件是用gbk编码
    imported_data = pd.read_csv('D:/1分钟数据压缩包/FutAC_Min1_Std_2016/ag主力连续.csv',encoding='gbk')
    # 将csv文件中 `市场代码`的 SC 替换成 Exchange.SHFE SHFE
    imported_data['市场代码'] = Exchange.SHFE
    # 增加一列数据 `inteval`，且该列数据的所有值都是 Interval.MINUTE
    imported_data['interval'] = Interval.MINUTE
    # 明确需要是float数据类型的列
    float_columns = ['开', '高', '低', '收', '成交量', '持仓量']
    for col in float_columns:
      imported_data[col] = imported_data[col].astype('float')
    # 明确时间戳的格式
    # %Y/%m/%d %H:%M:%S 代表着你的csv数据中的时间戳必须是 2020/05/01 08:32:30 格式
    datetime_format = '%Y%m%d %H:%M:%S'
    imported_data['时间'] = pd.to_datetime(imported_data['时间'],format=datetime_format)
    # 因为没有用到 成交额 这一列的数据，所以该列列名不变
    imported_data.columns = ['exchange','symbol','datetime','open','high','low','close','volume','成交额','open_interest','interval']
    imported_data['symbol'] ='ag88'
    move_df_to_mongodb(imported_data,'ag88')