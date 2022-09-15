from enum import Enum
import abc
from .rabbitmq_connector import RabbitMQConnector
import json

class BreadtAccount:
    def __init__(self, money) -> None:
        self.available_money = money


class BreadtBar:
    def __init__(
        self,
        close,
        datetime,
        high,
        last,
        low,
        open_price,
        symbol,
        prev_close,
        total_turnover,
        volume,
        period,
    ) -> None:
        self.close = close
        self.datetime = datetime
        self.high = high
        self.last = last
        self.low = low
        self.open = open_price
        self.symbol = symbol
        self.prev_close = prev_close
        self.total_turnover = total_turnover
        self.volume = volume
        self.period = period


class BreadtTick:
    def __init__(
        self, datetime, symbol, last, asks, bids, ask_vols, bid_vols, prev_close
    ) -> None:
        self.datetime = datetime
        self.last = last
        self.asks = asks
        self.bids = bids
        self.ask_vols = ask_vols
        self.bid_vols = bid_vols
        self.symbol = symbol
        self.prev_close = prev_close


class BreadtPosition:
    def __init__(self, quanty, available_quanty) -> None:
        self.quanty = quanty
        self.available_quanty = available_quanty


class BreadSignalOrderStatus(Enum):
    INIT = 0
    APPLY = 1
    DROP = 2
    SUBMIT = 3


class BreadtSignalDirect(Enum):
    BUY = 0
    SELL = 1
    CLOSE = 2
    BUY_ALL = 3


class BreadtSignalOrder:
    def __init__(
        self,
        bar,
        quanty,
        signal: BreadtSignalDirect,
        cprice,
        clprice,
        cslprice,
        sprice,
        feature,
        add,
        index,
        _id=None,
        is_order=False,
        is_close=False,
    ) -> None:
        self.datetime = bar.datetime

        self._id = bar.datetime.strftime("%Y%m%d%H%M%S")
        if _id is not None:
            self._id = _id

        self.price = bar.last
        self.quanty = quanty

        self.close = cprice
        self.close_with_low = clprice
        self.close_with_super_low = cslprice

        self.stop = sprice
        self.is_order = is_order
        self.is_close = is_close
        self.feature = feature
        self.status = BreadSignalOrderStatus.APPLY
        self.signal = signal
        self.close_direct = (
            BreadtSignalDirect.SELL
            if signal == BreadtSignalDirect.BUY
            else BreadtSignalDirect.BUY
        )
        self.direct = signal
        self.add = add
        self.index = index


class BreadtTradeOrder:
    def __init__(self, symbol, direct, price, quanty, datetime) -> None:
        self.symbol = symbol
        self.direct = direct
        self.price = price
        self.quanty = quanty
        self.datetime = datetime


class BreadtTradeContract:
    def __init__(self, order_id, symbol, direct, price, traded, total, dt, status) -> None:
        self.order_id = order_id
        self.symbol = symbol
        self.price = price
        self.traded = traded
        self.total = total
        self.direct = direct
        self.dt = dt
        self.status = status


class BreadtOptionDirect(Enum):
    OPEN = 0
    CLOSE = 1


class BreadtTradeTarget(Enum):
    ALL = 0
    SINGLE = 1

class BreadtTaskStatus(Enum):
    INIT = 0
    PROCESS = 1
    COMPLETED = 2

class BreadtTask(metaclass=abc.ABCMeta):
    def __init__(self, name, account, tasktype, symbol, quanty, step, time, ttype) -> None:
        self.name = name
        self.account = account
        self.tasktype = tasktype
        self.symbol = symbol
        self.quanty = quanty
        self.step = step
        self.time = time
        self.ttype = ttype
        self.process = 0.0
        self.status = BreadtTaskStatus.INIT
    
    def to_json(self):
        return {
           "account": self.account,
            "tasktype": self.tasktype.name(),
            "symbol": self.symbol,
            "quanty": self.quanty,
            "turnover": self.turnover,
            "time": self.time,
            "ttype": self.ttype.name()
        }
    
    @abc.abstractmethod
    def watch(self) -> None:
        pass

    @abc.abstractmethod
    def sync(self) -> None:
        pass

    def send_mq(self, configfile, exchange, routing_key, info) -> None:
        connector = RabbitMQConnector(configfile)
        connector.send_message(exchange, routing_key, json.dumps(info))

class BreadtTaskType(Enum):
    VENDOR = 0
    MANUAL = 1
    ALGOBYSIGNAL = 2

class BreadtTaskTimeType(Enum):
    DAILY = 0
    DURATION = 1
    ASAP = 2
    ALGO = 3