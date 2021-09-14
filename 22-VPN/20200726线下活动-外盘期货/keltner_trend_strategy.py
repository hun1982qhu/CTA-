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


class KeltnerTrendStrategy(CtaTemplate):
    """"""

    author = "用Python的交易员"

    kk_window = 5
    kk_dev = 1.3
    aroon_window = 2
    aroon_signal = 50
    trailing_percent = 1.2
    fixed_size = 1

    kk_up = 0
    kk_down = 0
    aroon_up = 0
    aroon_down = 0
    intra_trade_high = 0
    intra_trade_low = 0

    long_vt_orderids = []
    short_vt_orderids = []
    vt_orderids = []

    parameters = ["kk_window", "kk_dev", "aroon_window", "aroon_signal", "trailing_percent", "fixed_size"]
    variables = ["kk_up", "kk_down", "aroon_up", "aroon_down"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)

        self.am = ArrayManager()
        self.am5 = ArrayManager()

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
        self.bg.update_bar(bar)

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.aroon_up, self.aroon_down = self.am.aroon(self.aroon_window)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am5.update_bar(bar)
        if not self.am5.inited:
            return

        self.kk_up, self.kk_down = self.am5.keltner(self.kk_window, self.kk_dev)

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.aroon_up >= self.aroon_signal:
                self.buy(self.kk_up, self.fixed_size, True)
            elif self.aroon_down >= self.aroon_signal:
                self.short(self.kk_down, self.fixed_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * (1 - self.trailing_percent / 100)
            self.sell(long_stop, abs(self.pos), True)

        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            short_stop = self.intra_trade_low * (1 + self.trailing_percent / 100)
            self.cover(short_stop, abs(self.pos), True)
            
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
