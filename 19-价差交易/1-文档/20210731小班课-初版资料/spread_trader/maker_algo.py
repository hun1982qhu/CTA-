from typing import Any

from vnpy.trader.constant import Direction, Offset, Status
from vnpy.trader.object import (TickData, OrderData, TradeData)
from vnpy.trader.utility import round_to

from vnpy.app.spread_trading.template import SpreadAlgoTemplate
from vnpy.app.spread_trading.base import SpreadData


class SpreadMakerAlgo(SpreadAlgoTemplate):
    """"""
    algo_name = "SpreadMaker"

    def __init__(
        self,
        algo_engine: Any,
        algoid: str,
        spread: SpreadData,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        payup: int,
        interval: int,
        lock: bool,
        max_order_volume: float = 999,
        min_order_volume: float = 0
    ):
        """"""
        super().__init__(
            algo_engine, algoid, spread,
            direction, offset, price, volume,
            payup, interval, lock
        )

        self.cancel_interval: int = 2
        self.timer_count: int = 0

        self.max_order_volume = max_order_volume
        self.min_order_volume = min_order_volume

        self.active_quote_price: float = 0

        active_contract = self.get_contract(spread.active_leg.vt_symbol)
        self.active_price_tick: float = active_contract.pricetick

    def on_tick(self, tick: TickData):
        """"""
        # Return if tick not inited
        if not self.spread.bid_volume or not self.spread.ask_volume:
            return
        
        # Return if there are any existing orders
        if not self.check_hedge_order_finished():
            return
        
        # Hedge if active leg is not fully hedged
        if not self.check_hedge_finished():
            self.hedge_passive_legs()
            return

        # Check if re-quote is required
        new_quote_price = self.calculate_quote_price()

        if self.active_quote_price:
            price_change = self.active_quote_price - new_quote_price
            if abs(price_change) > (self.active_price_tick * self.payup):
                self.cancel_all_order()

            # Do not repeat sending quote orders
            return

        # Otherwise send active leg quote order
        self.quote_active_leg(new_quote_price)

    def on_order(self, order: OrderData):
        """"""
        # 遭遇拒单则停止策略
        if order.status == Status.REJECTED:
            self.stop()
            return

        # Only care active leg order update
        if order.vt_symbol != self.spread.active_leg.vt_symbol:
            return

        # Clear quote price record
        if not order.is_active():
            self.active_quote_price = 0

        # Do nothing if still any existing orders
        if not self.check_order_finished():
            return

        # Hedge passive legs if necessary
        if not self.check_hedge_finished():
            self.hedge_passive_legs()

    def on_trade(self, trade: TradeData):
        """"""
        pass

    def on_interval(self):
        """"""
        # Do nothing if only active leg quoting
        if self.check_hedge_finished():
            return

        # Cancel old hedge orders
        if not self.check_order_finished():
            self.cancel_all_order()

    def quote_active_leg(self, quote_price: float):
        """"""
        # Calculate spread order volume of new round trade
        spread_order_volume = self.target - self.traded

        if spread_order_volume > 0:
            spread_order_volume = min(
                spread_order_volume, self.max_order_volume)
        else:
            spread_order_volume = max(
                spread_order_volume, -self.max_order_volume)

        # localize object
        spread = self.spread

        # Calculate active leg order volume
        leg_order_volume = spread.calculate_leg_volume(
            spread.active_leg.vt_symbol,
            spread_order_volume
        )

        # Send active leg order
        self.send_leg_order(
            spread.active_leg.vt_symbol,
            leg_order_volume,
            quote_price
        )

        # Record current quote price
        self.active_quote_price = quote_price

    def hedge_passive_legs(self):
        """
        Send orders to hedge all passive legs.
        """
        # Calcualte spread volume to hedge
        active_leg = self.spread.active_leg
        active_traded = self.leg_traded[active_leg.vt_symbol]
        active_traded = round_to(active_traded, self.spread.min_volume)

        hedge_volume = self.spread.calculate_spread_volume(
            active_leg.vt_symbol,
            active_traded
        )

        # Calculate passive leg target volume and do hedge
        for leg in self.spread.passive_legs:
            passive_traded = self.leg_traded[leg.vt_symbol]
            passive_traded = round_to(passive_traded, self.spread.min_volume)

            passive_target = self.spread.calculate_leg_volume(
                leg.vt_symbol,
                hedge_volume
            )

            leg_order_volume = passive_target - passive_traded
            if leg_order_volume:
                self.send_leg_order(leg.vt_symbol, leg_order_volume)

    def send_leg_order(self, vt_symbol: str, leg_volume: float, leg_price: float = 0):
        """"""
        leg = self.spread.legs[vt_symbol]
        leg_tick = self.get_tick(vt_symbol)
        leg_contract = self.get_contract(vt_symbol)

        if leg_volume > 0:
            if leg_price:
                price = leg_price
            else:
                price = leg_tick.ask_price_1 + leg_contract.pricetick * self.payup
            self.send_long_order(leg.vt_symbol, price, abs(leg_volume))
        elif leg_volume < 0:
            if leg_price:
                price = leg_price
            else:
                price = leg_tick.bid_price_1 - leg_contract.pricetick * self.payup
            self.send_short_order(leg.vt_symbol, price, abs(leg_volume))

    def calculate_quote_price(self) -> float:
        """"""
        # Localize object
        spread = self.spread
        active_leg = spread.active_leg

        # Calculate active leg quote price
        price_multiplier = spread.price_multipliers[
            spread.active_leg.vt_symbol
        ]

        if self.direction == Direction.LONG:
            if price_multiplier > 0:
                quote_price = (self.price - spread.ask_price) / \
                    price_multiplier + active_leg.ask_price
                quote_price = min(quote_price, active_leg.ask_price - self.active_price_tick)
            else:
                quote_price = (self.price - spread.ask_price) / \
                    price_multiplier + active_leg.bid_price
                quote_price = max(quote_price, active_leg.bid_price + self.active_price_tick)
                
        else:
            if price_multiplier > 0:
                quote_price = (self.price - spread.bid_price) / \
                    price_multiplier + active_leg.bid_price
                quote_price = max(quote_price, active_leg.bid_price + self.active_price_tick)
            else:
                quote_price = (self.price - spread.bid_price) / \
                    price_multiplier + active_leg.ask_price
                quote_price = min(quote_price, active_leg.ask_price - self.active_price_tick)
            
        # Round price to pricetick of active leg
        contract = self.get_contract(active_leg.vt_symbol)
        quote_price = round_to(quote_price, contract.pricetick)

        return quote_price

    def check_hedge_order_finished(self):
        """"""
        finished = True

        for leg in self.spread.passive_legs:
            vt_orderids = self.leg_orders[leg.vt_symbol]

            if vt_orderids:
                finished = False
                break

        return finished
