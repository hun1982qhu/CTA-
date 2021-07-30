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


class DoubleChannelStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"

    boll_window = 22
    boll_dev = 3.4
    keltner_window = 24
    keltner_dev = 1
    cci_window = 6
    atr_window = 12
    risk_level = 5000

    boll_up = 0
    boll_down = 0
    keltner_up = 0
    keltner_down = 0
    cci_value = 0
    atr_value = 0
    trading_size = 1

    parameters = [
        "boll_window", "boll_dev", "cci_window", "keltner_window",
        "keltner_dev", "cci_window", "atr_window", "risk_level"
    ]

    variables = [
        "boll_up", "boll_down", "keltner_up", "keltner_down",
        "cci_value", "atr_value", "trading_size"
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

        self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
        self.keltner_up, self.keltner_down = am.keltner(
            self.keltner_window, self.keltner_dev)
        self.cci_value = am.cci(self.cci_window)

        if self.pos == 0:
            self.atr_value = am.atr(self.atr_window)
            self.trading_size = max(int(self.risk_level / self.atr_value), 1)

            if self.cci_value > 0:
                self.buy(self.boll_up, self.trading_size, True)
            elif self.cci_value < 0:
                self.short(self.boll_down, self.trading_size, True)

        elif self.pos > 0:
            self.sell(self.keltner_down, abs(self.pos), True)

        elif self.pos < 0:
            self.cover(self.keltner_up, abs(self.pos), True)

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
