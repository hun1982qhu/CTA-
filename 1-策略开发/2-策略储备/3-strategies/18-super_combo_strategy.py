from datetime import time

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    Direction,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.trader.constant import Interval


class SuperComboStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"

    # Parameters

    thrust_long = 0.34
    trailing_long = 0.35

    thrust_short = 0.4
    trailing_short = 0.8

    trading_size = 1

    # Variables
    day_open = 0
    day_high = 0
    day_low = 0
    sum_range = 0

    long_entry = 0
    short_entry = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0
    last_bar = None

    parameters = [
        "thrust_long", "trailing_long",
        "thrust_short", "trailing_short",
        "trading_size"
    ]

    variables = [
        "day_high", "day_low", "sum_range", "long_entry", "short_entry",
        "intra_trade_high", "intra_trade_low", "long_stop", "short_stop"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()

        if not self.last_bar:
            self.last_bar = bar
            return

        # For a new day, update all entry_range
        if bar.datetime.day != self.last_bar.datetime.day:
            self.sum_range = self.day_high - self.day_low
            self.day_open = bar.open_price
            self.day_high = bar.high_price
            self.day_low = bar.low_price

            long_entry_range = self.thrust_long * self.sum_range
            self.long_entry = self.day_open + long_entry_range

            short_entry_range = self.thrust_short * self.sum_range
            self.short_entry = self.day_open - short_entry_range
        # Otherwise update daily high/low price
        else:
            self.day_high = max(self.day_high, bar.high_price)
            self.day_low = min(self.day_low, bar.low_price)

            self.long_entry = max(self.long_entry, self.day_high)
            self.short_entry = min(self.short_entry, self.day_low)

        # Only open positions before 14:55
        if bar.datetime.time() < time(14, 55):
            # No pos
            if not self.pos:
                self.intra_trade_low = bar.low_price
                self.intra_trade_high = bar.high_price

                if bar.close_price > self.day_open:
                    self.buy(self.long_entry, self.trading_size, True, lock=True)
                else:
                    self.short(self.short_entry, self.trading_size, True, lock=True)
            # Long pos
            elif self.pos > 0:
                self.intra_trade_high = max(
                    self.intra_trade_high, bar.high_price)
                self.long_stop = self.intra_trade_high * \
                    (1 - self.trailing_long / 100)
                self.sell(self.long_stop, abs(self.pos), True, True)
            # Short pos
            else:
                self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
                self.short_stop = self.intra_trade_low * \
                    (1 + self.trailing_short / 100)
                self.cover(self.short_stop, abs(self.pos), True, True)
        # Close all positions after 14:55
        else:
            if self.pos > 0:
                self.sell(bar.close_price - 10, abs(self.pos), lock=True)
            elif self.pos < 0:
                self.cover(bar.close_price + 10, abs(self.pos), lock=True)

        self.last_bar = bar
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        pass

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
