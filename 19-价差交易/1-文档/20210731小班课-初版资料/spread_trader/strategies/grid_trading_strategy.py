from math import floor, ceil
from decimal import Decimal

from vnpy.app.spread_trading import (
    SpreadStrategyTemplate,
    SpreadAlgoTemplate,
    SpreadData,
    OrderData,
    TradeData,
    TickData,
    BarData
)
from vnpy.trader.utility import BarGenerator


class GridTradingStrategy(SpreadStrategyTemplate):
    """"""

    author = "用Python的交易员"

    pay_up = 10
    grid_start = 0.0
    grid_price = 50
    grid_volume = 5
    max_pos = 25

    current_grid = 0.0
    spread_pos = 0.0
    max_target = 0.0
    min_target = 0.0

    parameters = [
        "grid_start",
        "grid_price",
        "grid_volume",
        "max_pos"
    ]
    variables = [
        "spread_pos",
        "current_grid",
        "max_target",
        "min_target"
    ]

    def __init__(
        self,
        strategy_engine,
        strategy_name: str,
        spread: SpreadData,
        setting: dict
    ):
        """"""
        super().__init__(strategy_engine, strategy_name, spread, setting)

        self.bg = BarGenerator(self.on_spread_bar)

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

    def on_spread_data(self):
        """
        Callback when spread price is updated.
        """
        tick = self.get_spread_tick()
        self.on_spread_tick(tick)

    def on_spread_tick(self, tick: TickData):
        """
        Callback when new spread tick data is generated.
        """
        self.bg.update_tick(tick)

    def on_spread_bar(self, bar: BarData):
        """"""
        if not self.trading:
            return

        self.stop_all_algos()

        # 计算当前网格位置
        self.price_change = bar.close_price - self.grid_start       # 计算价格相比初始位置的变动
        self.current_grid = self.price_change / self.grid_price     # 计算网格水平

        # 计算当前最大、最小持仓
        self.max_target = ceil(-self.current_grid) * self.grid_volume
        self.max_target = min(self.max_target, self.max_pos)
        self.max_target = max(self.max_target, -self.max_pos)

        self.min_target = floor(-self.current_grid) * self.grid_volume
        self.min_target = min(self.min_target, self.max_pos)
        self.min_target = max(self.min_target, -self.max_pos)

        # 做多，检查最小持仓，和当前持仓的差值
        long_volume = self.min_target - self.spread_pos
        if long_volume > 0:
            long_price = bar.close_price + self.pay_up
            self.start_long_algo(long_price, long_volume, 5, 5)

        # 做空，检查最大持仓，和当前持仓的差值
        short_volume = self.max_target - self.spread_pos
        if short_volume < 0:
            short_price = bar.close_price - self.pay_up
            self.start_short_algo(short_price, abs(short_volume), 5, 5)
            self.start_short_algo(short_price, self.grid_volume, 5, 5)

        # 更新图形界面
        self.put_event()

    def on_spread_pos(self):
        """
        Callback when spread position is updated.
        """
        self.spread_pos = self.get_spread_pos()
        self.put_event()

    def on_spread_algo(self, algo: SpreadAlgoTemplate):
        """
        Callback when algo status is updated.
        """
        pass

    def on_order(self, order: OrderData):
        """
        Callback when order status is updated.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback when new trade data is received.
        """
        pass
