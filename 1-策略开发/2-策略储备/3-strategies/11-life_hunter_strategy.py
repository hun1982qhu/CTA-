import talib

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


class LifeHunterStrategy(CtaTemplate):
    """"""
    author = "super dino"

    entry_window = 28
    exit_window = 7
    fast_period = 12
    slow_period = 26
    signal_period = 9
    trend_level = 10
    atr_window = 4
    risk_level = 0.2
    trailing_tax = 0.3

    trading_size = 0
    entry_up = 0
    entry_down = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0
    MACD_sign = 0
    signal = 0
    hist = 0
    MACD_trend = 0
    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_out = 0
    short_out = 0

    parameters = [
        "entry_window",
        "exit_window",
        "fast_period",
        "slow_period",
        "signal_period",
        "trend_level",
        "atr_window",
        "risk_level",
        "trailing_tax"
    ]
    variables = [
        "trading_size",
        "entry_up",
        "entry_down",
        "exit_up",
        "exit_down",
        "atr_value",
        "MACD_sign",
        "signal",
        "hist",
        "MACD_trend",
        "long_entry",
        "short_entry",
        "long_stop",
        "short_stop",
        "intra_trade_high",
        "intra_trade_low",
        "long_out",
        "short_out"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar,30, self.on_30min_bar)

        self.am = ArrayManager()
        self.am30 = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(20)

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

        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am.inited or not self.am30.inited:
            return

        # No Position
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
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price           
            self.long_stop = 0
            self.short_stop = 0

            if self.MACD_trend > 0:
                self.buy(self.entry_up, self.trading_size, True)

            if self.MACD_trend < 0 :
                self.short(self.entry_down, self.trading_size, True)
        
        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.long_out = self.intra_trade_high * \
                (1 - self.trailing_tax / 100)
            sell_price = max(self.long_stop, self.exit_down, self.long_out)
            self.sell(sell_price, abs(self.pos), True)

        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.short_out = self.intra_trade_low * \
                (1 + self.trailing_tax / 100)
            cover_price = min(self.short_stop, self.exit_up, self.short_out)
            self.cover(cover_price, abs(self.pos), True)

        if bar.datetime.day == 21:
            print(bar.datetime, self.entry_up, bar.open_price, bar.high_price, bar.low_price, bar.close_price)

        self.put_event()


    def on_30min_bar(self, bar: BarData):
        """"""
        self.am30.update_bar(bar)
        if not self.am30.inited:
            return

        self.entry_up, self.entry_down = self.am30.donchian(self.entry_window)
        self.exit_up, self.exit_down = self.am30.donchian(self.exit_window)
        
        if bar.datetime.day == 21:
            print("on 30 min", bar.datetime, self.entry_up)
        self.MACD_sign,self.signal,self.hist = self.am30.macd(self.fast_period,self.slow_period,self.signal_period)
        self.MACD_sign = self.signal - self.hist

        if self.MACD_sign > self.trend_level:
            self.MACD_trend = 1
        elif self.MACD_sign < (-self.trend_level):
            self.MACD_trend = -1
        else:
            self.MACD_trend = 0

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


        msg = f"新的成交,策略是{self.strategy_name},方向{trade.direction}，开平{trade.offset}，当前仓位{self.pos}"
        self.send_email(msg)
        
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
