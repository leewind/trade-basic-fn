import pika
from .trading_system_basic import BreadtSignalDirect
from loguru import logger
from .rabbitmq_connector import RabbitMQConnector
import json


class TradeExecutor:
    def __init__(self, name, configfile, account_queue, order_exchange) -> None:
        self.name = name
        self.account_queue = account_queue
        self.order_exchange = order_exchange
        self.configfile = configfile
        self.positions = {}
        self.account = None
        pass

    def sync_account(self):
        """
        通过mq从qmt中获取账户信息
        """
        connector = RabbitMQConnector(self.configfile)
        connector.start_consume(self.account_queue, self.callback)

    def callback(self, ch, method, properties, body):
        info = json.loads(body)
        self.order(info["symbol"], info["price"], info["quanty"], info["ptype"])

    def buy(self, symbol, price, quanty, ptype):
        r = quanty
        if 1.002 * quanty * price > self.account.available_money:
            r = int(self.account.available_money / price / 100) * 100

        if r == 0:
            logger.error("资金不够购买{}".format(symbol))
            return None

        if (
            symbol.index("688") == 0
            and r < 200
            and self.account.available_money > 200 * price
        ):
            r = 200

        return {
            "direct": BreadtSignalDirect.BUY.name(),
            "symbol": symbol,
            "quanty": quanty,
            "price": price,
            "type": ptype,
        }

    def sell(self, symbol, price, quanty, ptype):
        if (
            symbol not in self.positions.names()
            or self.positions[symbol].available_quanty == 0
        ):
            logger.error("没有{}持仓".format(symbol))
            return

        r = quanty
        if r > self.positions[symbol].available_quanty:
            r = self.positions[symbol].available_quanty

        if (
            symbol.index("688") == 0
            and r < 200
            and self.positions[symbol].available_quanty > 200
        ):
            r = 200

        return {
            "direct": BreadtSignalDirect.SELL.name(),
            "symbol": symbol,
            "quanty": quanty,
            "price": price,
            "type": ptype,
        }

    def order(self, symbol, direct, price, quanty, ptype):
        if self.account is None:
            logger.error("没有获取到账号信息")
            return

        factory = {"BUY": self.buy, "SELL": self.sell}

        if direct.name() not in factory.keys():
            logger.error("direct方向没有确认")
            return

        o = factory[direct.name()](symbol, direct, price, quanty, ptype)
        connector = RabbitMQConnector(self.configfile)
        connector.send_message(
            self.order_exchange, "trader.{}".format(self.name), json.dumps(o)
        )

    def get_acount(self):
        return self.account

    def get_positions(self, symbol):
        if symbol not in self.positions:
            return None

        return self.positions[symbol]
