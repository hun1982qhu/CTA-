from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager
)


class CuatroStrategy(CtaTemplate):
    """"""
    author = "KeKe"

    rsi_signal = 19
    rsi_window = 14
    fast_window = 4
    slow_window = 26
    boll_window = 21
    boll_dev = 1.9
    trailing_short = 0.3
    trailing_long = 0.5
    fixed_size = 1

    boll_up = 0
    boll_down = 0
    rsi_value = 0
    rsi_long = 0
    rsi_short = 0
    fast_ma = 0
    slow_ma = 0
    ma_trend = 0
    long_stop = 0
    short_stop = 0
    intra_trade_high = 0
    intra_trade_low = 0

    parameters = [
        "rsi_signal", "rsi_window",
        "fast_window", "slow_window",
        "boll_window", "boll_dev",
        "trailing_long", "trailing_short",
        "fixed_size"
    ]

    variables = [
        "boll_up", "boll_down",
        "rsi_value", "rsi_long", "rsi_short",
        "fast_ma", "slow_ma", "ma_trend",
        "long_stop", "short_stop"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(CuatroStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.rsi_long = 50 + self.rsi_signal
        self.rsi_short = 50 - self.rsi_signal

        self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am5 = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am15 = ArrayManager()

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
        self.bg5.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg5.update_bar(bar)
        self.bg15.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am5.update_bar(bar)
        if not self.am5.inited:
            return

        if not self.ma_trend:
            return

        self.rsi_value = self.am5.rsi(self.rsi_window)
        self.boll_up, self.boll_down = self.am5.boll(
            self.boll_window, self.boll_dev)
        boll_width = self.boll_up - self.boll_down

        if self.pos == 0:
            self.intra_trade_low = bar.low_price
            self.intra_trade_high = bar.high_price

            if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
                self.buy(self.boll_up, self.fixed_size, True)

            elif self.ma_trend < 0 and self.rsi_value <= self.rsi_short:
                self.short(self.boll_down, self.fixed_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.long_stop = (self.intra_trade_high -
                              self.trailing_long * boll_width)
            self.sell(self.long_stop, abs(self.pos), True, True)

        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.short_stop = (self.intra_trade_low +
                               self.trailing_short * boll_width)
            self.cover(self.short_stop, abs(self.pos), True, True)

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
        else:
            self.ma_trend = -1

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
