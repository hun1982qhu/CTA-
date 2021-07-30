#%%
import talib
import datetime
import time
import openpyxl

from openpyxl.utils import get_column_letter
from pathlib import Path
from datetime import time as time1
from typing import Callable

from vnpy_ctastrategy import CtaTemplate
from vnpy_ctastrategy.base import StopOrder, StopOrderStatus

from vnpy.trader.object import TickData, BarData, OrderData, TradeData
from vnpy.trader.constant import Interval, Exchange, Status
from vnpy.trader.utility import BarGenerator, ArrayManager


#%%
class SuperTurtleStrategyHNTest(CtaTemplate):
    """"""
    author = "Huang Ning"

    entry_window = 28
    exit_window = 7
    atr_window = 4
    risk_level = 0.2

    trading_size = 0
    entry_up = 0
    entry_down = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0

    parameters = [
        "entry_window",
        "exit_window",
        "atr_window",
        "risk_level"
    ]
    variables = [
        "entry_up",
        "entry_down", 
        "exit_up",
        "exit_down", 
        "trading_size", 
        "atr_value"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = XminBarGenerator(self.on_bar, 1, self.on_hour_bar, interval=Interval.HOUR)
        self.am = ArrayManager()

        self.liq_price = 0
        self.trading_size = 0

        self.on_bar_time = time1(0, 0)
        self.clearance_time = time1(14, 57)
        self.liq_time = time1(14, 59)

        self.day_clearance = False

        self.buy_svt_orderids = []
        self.sell_svt_orderids = []
        self.short_svt_orderids = []
        self.cover_svt_orderids = []

        self.sell_lvt_orderids = []
        self.cover_lvt_orderids = []

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(20)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        self.liq_price = bar.close_price
        self.on_bar_time = bar.datetime.time()
        self.on_bar_date = bar.datetime.date()

        # 2021年5月10日有极端行情，收益异常高，不具有普遍参考价值，因此在回测中跳过这一天
        extreme_date = "2021-05-10"
        extreme_date = time.strptime(extreme_date, "%Y-%m-%d")
        year, month, day = extreme_date[:3]
        extreme_date = datetime.date(year, month, day)
        
        self.day_clearance = (self.clearance_time <= self.on_bar_time <= self.liq_time)

        if self.on_bar_date != extreme_date:

            self.bg.update_bar(bar)

            if self.day_clearance:

                if not self.buy_svt_orderids and not self.short_svt_orderids\
                    and not self.sell_svt_orderids and not self.cover_svt_orderids\
                        and not self.sell_lvt_orderids and not self.cover_lvt_orderids:
                        
                        if self.pos > 0:
                            self.sell_lvt_orderids = self.sell(self.liq_price - 5, abs(self.pos))

                        elif self.pos < 0:
                            self.cover_lvt_orderids = self.cover(self.liq_price + 5, abs(self.pos))

                else:
                    for buf_orderids in [
                        self.buy_svt_orderids,
                        self.sell_svt_orderids,
                        self.short_svt_orderids,
                        self.cover_svt_orderids,
                        self.sell_lvt_orderids,
                        self.cover_lvt_orderids
                    ]:

                        if buf_orderids:
                            for vt_orderid in buf_orderids:
                                self.cancel_order(vt_orderid)

    def on_hour_bar(self, bar: BarData):
        """"""

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.entry_up, self.entry_down = self.am.donchian(self.entry_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)

        if not self.day_clearance:
            if not self.pos:
                self.atr_value = self.am.atr(self.atr_window)

                if self.atr_value == 0:
                    return

                atr_risk = talib.ATR(
                    1 / self.am.high,
                    1 / self.am.low,
                    1 / self.am.close,
                    self.atr_window
                )[-1]
                self.trading_size = max(int(self.risk_level / atr_risk), 1)

                self.long_entry = 0
                self.short_entry = 0
                self.long_stop = 0
                self.short_stop = 0

                self.buy(self.entry_up, self.trading_size, True)
                self.short(self.entry_down, self.trading_size, True)

            elif self.pos > 0:
                sell_price = max(self.long_stop, self.exit_down)
                self.sell(sell_price, abs(self.pos), True)

            elif self.pos < 0:
                cover_price = min(self.short_stop, self.exit_up)
                self.cover(cover_price, abs(self.pos), True)

        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price
            self.long_stop = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + 2 * self.atr_value

        self.sync_data()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass


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