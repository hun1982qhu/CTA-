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
from vnpy.trader.constant import Interval


class KeltnerBanditStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"

    kk_window = 20
    kk_dev = 2
    cci_window = 10
    cci_stop = 44
    atr_window = 10
    risk_level = 5000

    trading_size = 0
    kk_up = 0
    kk_down = 0
    cci_value = 0
    atr_value = 0

    parameters = [
        "kk_window", "kk_dev", "cci_window",
        "cci_stop", "atr_window", "risk_level"
    ]
    variables = [
        "trading_size", "kk_up", "kk_down",
        "cci_value", "atr_value"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(
            self.on_bar, 1, self.on_hour_bar, interval=Interval.HOUR)
        self.am = ArrayManager()

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

    def on_hour_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.kk_up, self.kk_down = am.keltner(self.kk_window, self.kk_dev)
        self.cci_value = am.cci(self.cci_window)

        if self.pos == 0:
            atr_value = am.atr(self.atr_window)
            self.trading_size = max(int(self.risk_level / atr_value), 1)

            self.buy(self.kk_up, self.trading_size, True)
            self.short(self.kk_down, self.trading_size, True)

        elif self.pos > 0:
            if self.cci_value < - self.cci_stop:
                self.sell(bar.close_price - 10, abs(self.pos), False)

        elif self.pos < 0:
            if self.cci_value > self.cci_stop:
                self.cover(bar.close_price + 10, abs(self.pos), False)

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
