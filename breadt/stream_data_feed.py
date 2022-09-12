import abc
from .rabbitmq_connector import RabbitMQConnector
import pandas as pd
import warnings

warnings.filterwarnings("ignore")


class StreamDataFeed(metaclass=abc.ABCMeta):
    def __init__(self, configfile, exchange) -> None:
        self.configfile = configfile
        self.exchange = exchange

    def send_message(self, routing_key, context) -> None:
        connector = RabbitMQConnector(self.configfile)
        connector.send_message(self.exchange, routing_key, context)

    @abc.abstractmethod
    def watch(self) -> None:
        pass
