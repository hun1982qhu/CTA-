import multiprocessing
import sys
from time import sleep
from datetime import datetime, time
from logging import INFO

from vnpy.event import EventEngine
from vnpy.app.paper_account import PaperAccountApp
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine

from vnpy.gateway.ctp import CtpGateway
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctastrategy.base import EVENT_CTA_LOG

SETTINGS["log.active"] = True  # 是否记录日志
SETTINGS["log.level"] = INFO  # 日志的详细程度，INFO是最低程度的，但也会记录大多数的日志
SETTINGS["log.console"] = True  # 是否将日志在CMD中逐条打出


ctp_setting = {
    "用户名": "167465",
    "密码": "hun829248",
    "经纪商代码": "9999",
    "交易服务器": "180.168.146.187:10202",
    "行情服务器": "180.168.146.187:10212",
    "产品名称": "simnow_client_test",
    "授权编码": "0000000000000000",
    "产品信息": "simnow_client_test"
}


# Chinese futures market trading period (day/night)
DAY_START = time(8, 45)
DAY_END = time(15, 1)

NIGHT_START = time(20, 45)
NIGHT_END = time(2, 45)


def check_trading_period():
    """"""
    current_time = datetime.now().time()

    trading = False

    if (
        (DAY_START <= current_time <= DAY_END)
        or (current_time >= NIGHT_START)
        or (current_time <= NIGHT_END)
    ):
        trading = True

    return trading


def run_child():
    """
    Running in the child process.
    """

    SETTINGS["log.file"] = True

    # 创建主引擎
    event_engine = EventEngine()  # 创建时间引擎
    main_engine = MainEngine(event_engine)  # 主引擎是事件驱动的，因此只有event_engine这一个入参
    main_engine.add_gateway(CtpGateway)  # 主引擎添加CTP服务器接口
    cta_engine = main_engine.add_app(CtaStrategyApp)  # 主引擎添加CtaStrategyApp，即创建了cta_engine
    paper_engine = main_engine.add_app(PaperAccountApp)  # 主引擎添加PaperAccountApp，即创建了paper_engine

    # paper_engine.trade_slippage = 0.2
    # paper_engine.timer_interval = 3
    # paper_engine.instant_trade = False
    # paper_engine.save_setting()

    main_engine.write_log("主引擎创建成功")  # 上述步骤全部完成即创建了主引擎

    # 创建日志引擎
    log_engine = main_engine.get_engine("log")
    event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
    main_engine.write_log("注册日志事件监听")

    # 连接CTP服务器
    main_engine.connect(ctp_setting, "CTP")
    main_engine.write_log("连接CTP接口")
    sleep(10)

    # 初始化CTA引擎
    cta_engine.init_engine()
    main_engine.write_log("CTA引擎初始化完成")

    # 初始化交易策略
    HNstrategy_name = "papertest1"
    cta_engine.init_strategy(HNstrategy_name)
    sleep(20)   # Leave enough time to complete strategy initialization
    main_engine.write_log(f"{HNstrategy_name}完成初始化")

    # 启动交易策略
    cta_engine.start_strategy(HNstrategy_name)
    main_engine.write_log(f"{HNstrategy_name}已启动")
    current_time = datetime.now().time()
    
    # 发送邮件通知
    main_engine.send_email(
        "终极震荡指标策略-papertest1启动", 
        f"trading started, {current_time}", 
        SETTINGS["email.receiver"])

    while True:
        sleep(10)

        trading = check_trading_period()
        if not trading:
            
            print("关闭子进程")
            
            current_time = datetime.now().time()
            
            main_engine.send_email(
                "终极震荡指标策略关闭", 
                f"trading closed, {current_time}", 
                SETTINGS["email.receiver"])
            
            main_engine.close()
            
            sys.exit(0)


def run_parent():
    """
    Running in the parent process.
    """
    print("启动CTA策略守护父进程")

    child_process = None

    while True:
        trading = check_trading_period()

        # Start child process in trading period
        if trading and child_process is None:
            print("启动子进程")
            child_process = multiprocessing.Process(target=run_child)
            child_process.start()
            print("子进程启动成功")

        # 非记录时间则退出子进程
        if not trading and child_process is not None:
            if not child_process.is_alive():
                child_process = None
                print("子进程关闭成功")

        sleep(5)


if __name__ == "__main__":
    run_parent()