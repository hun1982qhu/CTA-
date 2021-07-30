#%%
from typing import Any, Callable
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TradeData,
    StopOrder,
    OrderData
)
from vnpy.app.cta_strategy.base import StopOrderStatus, BacktestingMode, EngineType
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.trader.object import BarData, TickData
from vnpy.trader.constant import Interval, Offset, Direction, Exchange, Status
import numpy as np
import pandas as pd
from datetime import time as time1
from datetime import datetime
import time
import talib

from vnpy.trader.ui import create_qapp, QtCore
from vnpy.chart import ChartWidget, VolumeItem, CandleItem

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style
mpl.rcParams['font.family'] = 'serif'  # 解决一些字体显示乱码的问题

style.use('ggplot')
import seaborn as sns

sns.set()

#%%
class CuatroStrategy(CtaTemplate):
    """"""
    boll_window = 20
    boll_dev = 2
    rsi_window = 14
    rsi_signal = 30
    fast_window = 5
    slow_window = 20
    trailing_long = 1
    trailing_short = 1
    fixed_size = 1

    boll_up = 0
    boll_down = 0
    rsi_value = 0
    rsi_long = 0
    rsi_short = 0
    fast_ma = 0
    slow_ma = 0
    ma_trend = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0

    author = "huang ning"
    parameters = [
        "boll_window",
        "boll_dev",
        "rsi_window",
        "rsi_signal",
        "fast_window",
        "slow_window",
        "trailing_long",
        "trailing_short",
        "fixed_size"
    ]
    variables = [
        "boll_up",
        "boll_down",
        "rsi_value",
        "rsi_long",
        "rsi_short",
        "fast_ma",
        "slow_ma",
        "ma_trend",
        "intra_trade_high",
        "intra_trade_low",
        "long_stop",
        "short_stop"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.rsi_long = 50 + self.rsi_signal
        self.rsi_short = 50 - self.rsi_signal

        self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar)

        self.am5 = ArrayManager()
        self.am15 = ArrayManager()
   
    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(10)
 
    def on_start(self):
        """"""
        self.write_log("策略启动")
  
    def on_stop(self):
        """"""
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """"""
        self.bg5.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        self.bg5.update_bar(bar)
        self.bg15.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am5.update_bar(bar)
        if not self.am5.inited or not self.am15.inited:
            return

        self.boll_up, self.boll_down = self.am5.boll(self.boll_window, self.boll_dev)
        self.rsi_value = self.am5.rsi(self.rsi_window)

        # 计算布林带有两种方法
        boll_width = self.boll_up - self.boll_down
        # boll_width = self.am5.std(self.boll_window) * self.boll_dev * 2 因为这种算法相比第一种运算速度慢，所以一般使用上一种方法

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price
            self.long_stop = 0
            self.stop_stop = 0

            if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
                self.buy(self.boll_up, self.fixed_size, stop=True)
            elif self.ma_trend < 0 and self.rsi_value <= self.rsi_short:
                self.short(self.boll_down, self.fixed_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.long_stop = (self.intra_trade_high - self.trailing_long * boll_width)
            self.sell(self.long_stop, abs(self.pos), stop=True)
            
        else:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.short_stop = (self.intra_trade_low + self.trailing_short * boll_width)
            self.cover(self.short_stop, abs(self.pos), stop=True)

        self.put_event()

    def on_15min_bar(self, bar: BarData):
        """"""
        self.am15.update_bar(bar)
        if not self.am15.inited:
            return

        self.fast_ma = self.am15.sma(self.fast_window)
        self.slow_ma = self.am15.sma(self.slow_window)

        if self.fast_ma > self.slow_ma:
            self.ma_trend = 1
        elif self.fast_ma < self.slow_ma:
            self.ma_trend = -1
        else:
            self.ma_trend = 0

        self.put_event()

    def on_trade(self, trade: TradeData):
        """"""
        self.put_event()

    def on_order(self, order: OrderData):
        """"""
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """"""
        self.put_event()

#%%
start1 = time.time()
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="IF888.CFFEX",
    interval="1m",
    start=datetime(2020, 1, 1),
    end=datetime(2021, 1, 1),
    rate=0.0001,
    slippage=2.0,
    size=10,
    pricetick=1.0,
    capital=50000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(CuatroStrategy, {})
#%%
start2 = time.time()
engine.load_data()
end2 = time.time()
print(f"加载数据所需时长: {(end2-start2)} Seconds")
#%%
engine.run_backtesting()
#%%
engine.calculate_result()
engine.calculate_statistics()
# 待测试的代码
end1 = time.time()
print(f"单次回测运行时长: {(end1-start1)} Seconds")
engine.show_chart()
#%%
# setting = OptimizationSetting()
# setting.set_target("end_balance")
# setting.add_parameter("bar_window_length", 1, 60, 1)
# setting.add_parameter("cci_window", 1, 60, 1)
# setting.add_parameter("pricetick_multilplier1", 1, 10, 1)
# setting.add_parameter("macd_fastk_period", 4, 20, 2)
# setting.add_parameter("macd_slowk_period", 21, 30, 1)
# setting.add_parameter("macd_signal_period", 4, 12, 2)
#%%
# engine.run_optimization(setting, output=True)