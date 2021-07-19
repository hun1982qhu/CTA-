# flake8: noqa
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy.gateway.ctp import CtpGateway
from vnpy.gateway.okexs import OkexsGateway
from vnpy.gateway.binance import BinanceGateway
from vnpy.app.spread_trading import SpreadTradingApp
from vnpy.app.risk_manager import RiskManagerApp

from maker_algo import SpreadMakerAlgo
from vnpy.app.spread_trading.engine import SpreadAlgoEngine
SpreadAlgoEngine.algo_class = SpreadMakerAlgo


def main():
    """"""
    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(CtpGateway)
    main_engine.add_gateway(BinanceGateway)
    main_engine.add_gateway(OkexsGateway)

    main_engine.add_app(SpreadTradingApp)
    main_engine.add_app(RiskManagerApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
