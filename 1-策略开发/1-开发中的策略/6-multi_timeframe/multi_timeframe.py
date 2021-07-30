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
from vnpy.app.cta_strategy.base import StopOrderStatus, BacktestingMode
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.trader.object import BarData, TickData
from vnpy.trader.constant import Interval, Offset, Direction, Exchange, Status
import numpy as np
import pandas as pd
from datetime import time as time1
from datetime import datetime
import time
import talib
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style
mpl.rcParams['font.family'] = 'serif'  # 解决一些字体显示乱码的问题

style.use('ggplot')
import seaborn as sns

sns.set()


#%%
class MultiTimeframeStrategyHNTest(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window1 = 5
    bar_window2 = 15
    rsi_signal = 20
    rsi_window = 14
    fast_window = 12
    slow_window = 20
    fixed_size = 1
    pricetick_multiplier1 = 0.2
    pricetick_multiplier2 = 0

    rsi_value = 0
    rsi_long = 0
    rsi_short = 0
    fast_ma = 0
    slow_ma = 0
    ma_trend = 0

    parameters = [
        "bar_window1",
        "bar_window2",
        "rsi_signal",
        "rsi_window",
        "fast_window",
        "slow_window",
        "fixed_size",
        "pricetick_multiplier1",
        "pricetick_multiplier2"
    ]

    variables = [
        "rsi_value",
        "rsi_long",
        "rsi_short",
        "fast_ma",
        "slow_ma",
        "ma_trend"
    ]


    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.pricetick = self.get_pricetick()

        self.rsi_long = 50 + self.rsi_signal
        self.rsi_short = 50 - self.rsi_signal

        self.bg1 = XminBarGenerator(self.on_bar, self.bar_window1, self.on_Xmin1_bar)
        self.am1 = ArrayManager()

        self.bg2 = XminBarGenerator(self.on_bar, self.bar_window2, self.on_Xmin2_bar)
        self.am2 = ArrayManager()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.buy_price = 0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

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
        self.bg1.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        # 注意：不同周期K线合成的顺序对结果是有影响的
        self.bg1.update_bar(bar)
        self.bg2.update_bar(bar)

        if self.buy_vt_orderids:
            for vt_orderid in self.buy_vt_orderids:
                self.cancel_order(vt_orderid)
            self.buy_vt_orderids = self.buy(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)     
        
        elif self.sell_vt_orderids:
            for vt_orderid in self.sell_vt_orderids:
                self.cancel_order(vt_orderid)
            self.sell_vt_orderids = self.sell(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
        
        elif self.short_vt_orderids:
            for vt_orderid in self.short_vt_orderids:
                self.cancel_order(vt_orderid)
            self.short_vt_orderids = self.short(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
        
        elif self.cover_vt_orderids:
            for vt_orderid in self.cover_vt_orderids:
                self.cancel_order(vt_orderid)
            self.cover_vt_orderids = self.cover(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

    def on_Xmin1_bar(self, bar: BarData):
        """"""
        self.am1.update_bar(bar)
        if not self.am1.inited:
            return

        if not self.ma_trend:
            return

        self.rsi_value = self.am1.rsi(self.rsi_window)

        if self.pos == 0:
            self.buy_price = bar.close_price + self.pricetick * self.pricetick_multiplier1
            self.sell_price = 0
            self.short_price = bar.close_price - self.pricetick * self.pricetick_multiplier1
            self.cover_price = 0
        
        elif self.pos > 0:
            self.buy_price = 0
            self.sell_price = bar.close_price - self.pricetick * self.pricetick_multiplier1
            self.short_price = 0
            self.cover_price = 0

        else:
            self.buy_price = 0
            self.sell_price = 0
            self.short_price = 0
            self.cover_price = bar.close_price + self.pricetick * self.pricetick_multiplier1

        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
                    self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0
            else:
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)

            if not self.short_vt_orderids:
                if self.ma_trend < 0 and self.rsi_value <= self.rsi_short:
                    self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0
            else:
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)
        
        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.ma_trend < 0 or self.rsi_value < 50:
                    self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)

        else:
            if not self.cover_vt_orderids:
                if self.ma_trend > 0 or self.rsi_value > 50:
                    self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)

    def on_Xmin2_bar(self, bar: BarData):
        """"""
        self.am2.update_bar(bar)
        if not self.am2.inited:
            return
        
        self.fast_ma = self.am2.sma(self.fast_window)
        self.slow_ma = self.am2.sma(self.slow_window)

        if self.fast_ma > self.slow_ma:
            self.ma_trend = 1
        elif self.fast_ma < self.slow_ma:
            self.ma_trend = -1
        else:
            self.ma_trend = 0

    def on_stop_order(self, stop_order: StopOrder):
        """"""
        if stop_order.status == StopOrderStatus.WAITING:
            return

        for buf_orderids in [
            self.buy_vt_orderids, 
            self.sell_vt_orderids, 
            self.short_vt_orderids, 
            self.cover_vt_orderids
        ]:
            if stop_order.stop_orderid in buf_orderids:
                buf_orderids.remove(stop_order.stop_orderid)


class XminBarGenerator(BarGenerator):
    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        super().__init__(on_bar, window, on_window_bar, interval)
    
    def update_bar(self, bar: BarData) ->None:
        """
        Update 1 minute bar into generator
        """
        # If not inited, creaate window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest

        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            # if not (bar.datetime.minute + 1) % self.window:
            #     finished = True
            
            self.interval_count += 1

            if not self.interval_count % self.window:
                finished = True
                self.interval_count = 0

            elif bar.datetime.time() in [time1(10, 14), time1(11, 29), time1(14, 59), time1(22, 59)]:
                if bar.exchange in [Exchange.SHFE, Exchange.DCE, Exchange.CZCE]:
                    finished = True
                    self.interval_count = 0

        elif self.interval == Interval.HOUR:
            if self.last_bar:
                new_hour = bar.datetime.hour != self.last_bar.datetime.hour
                last_minute = bar.datetime.minute == 59
                not_first = self.window_bar.datetime != bar.datetime

                # To filter duplicate hour bar finished condition
                if (new_hour or last_minute) and not_first:
                    # 1-hour bar
                    if self.window == 1:
                        finished = True
                    # x-hour bar
                    else:
                        self.interval_count += 1

                        if not self.interval_count % self.window:
                            finished = True
                            self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar

#%%
start1 = time.time()
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb888.SHFE",
    interval="1m",
    start=datetime(2017, 10, 15),
    end=datetime(2020,10,15),
    rate=0.0001,
    slippage=2,
    size=10,
    pricetick=1,
    capital=1_000_000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(MultiTimeframeStrategyHNTest, {})
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
# setting.add_parameter("bar_window_length", 1, 20, 1)
# setting.add_parameter("cci_window", 3, 10, 1)
# setting.add_parameter("fixed_size", 1, 1, 1)
# setting.add_parameter("sell_multipliaer", 0.80, 0.99, 0.01)
# setting.add_parameter("cover_multiplier", 1.01, 1.20, 0.01)
# setting.add_parameter("pricetick_multiplier", 1, 5, 1)
#%%
# engine.run_optimization(setting, output=True)
# %%