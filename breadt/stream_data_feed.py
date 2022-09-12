import abc
from .rabbitmq_connector import RabbitMQConnector
import datetime
import pandas as pd
from os.path import exists
import tushare as ts
import warnings

warnings.filterwarnings("ignore")

TUSHARE_KEY = "32edd62d8ec424bd141e2992ffd0725c51b246e205115188d1576229"


class StreamDataFeed(metaclass=abc.ABCMeta):
    def __init__(self, configfile, exchange) -> None:
        self.configfile = configfile
        self.exchange = exchange

        ts.set_token(TUSHARE_KEY)
        self.pro = ts.pro_api()

    def is_in_trading_time(self) -> bool:
        ct = datetime.datetime.now()
        hm = int(ct.strftime("%H%M"))
        if (hm >= 930 and hm <= 1130) or (hm >= 1300 and hm <= 1500):
            return True

        return False

    def is_after_trading_time(self) -> bool:
        ct = datetime.datetime.now()
        if ct.hour > 14:
            return True

        return False

    def read_from_cache(self, dt) -> pd.DataFrame:
        filename = "trading_date.csv"
        if not exists(filename):
            df = self.pro.trade_cal(exchange="", start_date=dt, end_date=dt)
            df.to_csv(filename, index=False)
            return df

        df = pd.read_csv(filename)
        if len(df[df["cal_date"] == dt]) == 0:
            df = self.pro.trade_cal(exchange="", start_date=dt, end_date=dt)
            df.to_csv(filename, index=False)

        return df

    def is_in_trading_day(self) -> bool:
        ct = datetime.datetime.now()
        dt = int(ct.strftime("%Y%m%d"))

        df = self.read_from_cache(dt)

        if df is None or len(df) == 0:
            return False

        return df[df["cal_date"] == dt].iloc[0]["is_open"] > 0

    def send_message(self, routing_key, context) -> None:
        connector = RabbitMQConnector(self.configfile)
        connector.send_message(self.exchange, routing_key, context)

    @abc.abstractmethod
    def watch(self) -> None:
        pass
