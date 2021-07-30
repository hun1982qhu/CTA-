from datetime import time
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class ImprovedDtStrategy(CtaTemplate):
    """"""

    author = "用Python的交易员"

    fixed_size = 1
    k1 = 0.15
    k2 = 0.25
    rsi_window = 30
    rsi_signal = 10
    trailing_long = 0.8
    trailing_short = 1.4

    daily_limit = 0

    day_open = 0
    day_high = 0
    day_low = 0

    day_range = 0
    long_entry = 0
    short_entry = 0

    intra_trade_high = 0
    intra_trade_low = 0

    daily_count = 0

    parameters = [
        "k1",
        "k2",
        "rsi_window",
        "rsi_signal",
        "trailing_long",
        "trailing_short",
        "fixed_size"
    ]
    variables = ["day_range", "long_entry", "short_entry"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.last_bar = None

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

        self.am.update_bar(bar)

        # 计算DT范围
        if not self.last_bar:
            self.last_bar = bar
            return

        if self.last_bar.datetime.date() != bar.datetime.date():
            if self.day_high:
                self.day_range = self.day_high - self.day_low
                self.long_entry = bar.open_price + self.k1 * self.day_range
                self.short_entry = bar.open_price - self.k2 * self.day_range

            self.day_open = bar.open_price
            self.day_high = bar.high_price
            self.day_low = bar.low_price

            self.long_entered = False
            self.short_entered = False

            self.daily_count = 0
        else:
            self.day_high = max(self.day_high, bar.high_price)
            self.day_low = min(self.day_low, bar.low_price)

        self.last_bar = bar

        if not self.day_range or not self.am.inited:
            return

        # 计算技术指标
        rsi_value = self.am.rsi(self.rsi_window)

        # 交易逻辑执行
        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.daily_count < self.daily_limit:
                if rsi_value >= 50 + self.rsi_signal:
                    self.buy(self.long_entry, self.fixed_size, True)
                elif rsi_value <= 50 - self.rsi_signal:
                    self.short(self.short_entry, self.fixed_size, True)
        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * (1 - self.trailing_long / 100)
            long_stop = max(long_stop, self.short_entry)
            self.sell(long_stop, self.fixed_size, True)

            self.short(self.short_entry, self.fixed_size, True)

        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            short_stop = self.intra_trade_low * (1 + self.trailing_short / 100)
            short_stop = min(short_stop, self.long_entry)
            self.cover(short_stop, self.fixed_size, True)

            self.buy(self.long_entry, self.fixed_size, True)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
