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
from vnpy.app.cta_strategy.base import EngineType
from vnpy.trader.constant import Interval


class RsiMomentumStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"

    atr_window = 16
    atr_ma_window = 10
    rsi_window = 4
    rsi_entry = 19
    risk_level = 5000
    exit_window = 20

    trading_size = 0
    target_pos = 0
    atr_value = 0
    atr_ma = 0
    rsi_value = 0
    rsi_long = 0
    rsi_short = 0

    parameters = [
        "atr_window", "atr_ma_window", "rsi_window",
        "rsi_entry", "exit_window"
    ]
    variables = [
        "atr_value", "atr_ma", "rsi_value", "rsi_long", "rsi_short",
        "target_pos"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(
            self.on_bar, 1, self.on_hour_bar, interval=Interval.HOUR)
        self.am = ArrayManager()

        self.engine_type = self.get_engine_type()
        self.vt_orderids = []
        self.order_price = 0

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        self.rsi_long = 50 + self.rsi_entry
        self.rsi_short = 50 - self.rsi_entry

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

        # 只有实盘交易才使用BestLimit算法
        if self.engine_type != EngineType.LIVE:
            return

        order_volume = self.target_pos - self.pos
        if not order_volume:
            return

        if order_volume > 0:
            if not self.vt_orderids:
                self.order_price = tick.bid_price_1
                vt_orderids = self.buy(
                    self.order_price, abs(order_volume))
                self.vt_orderids.extend(vt_orderids)
            elif self.order_price != tick.bid_price_1:
                for vt_orderid in self.vt_orderids:
                    self.cancel_order(vt_orderid)

        elif order_volume < 0:
            if not self.vt_orderids:
                self.order_price = tick.ask_price_1
                vt_orderids = self.short(
                    self.order_price, abs(order_volume)
                )
                self.vt_orderids.extend(vt_orderids)
            elif self.order_price != tick.ask_price_1:
                self.cancel_order(self.vt_orderid)

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

        atr_array = am.atr(self.atr_window, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_ma_window:].mean()
        self.rsi_value = am.rsi(self.rsi_window)
        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)

        if self.pos == 0:
            self.trading_size = max(int(self.risk_level / self.atr_value), 1)

            if self.atr_value > self.atr_ma:
                if self.rsi_value > self.rsi_long:
                    if self.engine_type == EngineType.BACKTESTING:
                        self.buy(bar.close_price + 5, self.trading_size)
                    else:
                        self.target_pos = self.trading_size

                elif self.rsi_value < self.rsi_short:
                    if self.engine_type == EngineType.BACKTESTING:
                        self.short(bar.close_price - 5, self.trading_size)
                    else:
                        self.target_pos = -self.trading_size

        elif self.pos > 0:
            self.sell(self.exit_down, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.cover(self.exit_up, abs(self.pos), stop=True)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        # 只有实盘交易才使用BestLimit算法
        if self.engine_type != EngineType.LIVE:
            return

        if not order.is_active() and order.vt_orderid in self.vt_orderids:
            self.vt_orderids.remove(order.vt_orderid)

            if not self.vt_orderids:
                self.order_price = 0

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
