import abc
from .rabbitmq_connector import RabbitMQConnector
from .dingtalk_alert import DingTalkAlert
import json


class Strategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def monitor(self) -> None:
        pass

    def send_mq(self, configfile, exchange, routing_key, info) -> None:
        connector = RabbitMQConnector(configfile)
        connector.send_message(exchange, routing_key, json.dumps(info))

    def send_alert(self, secret, access_token, context) -> None:
        ding = DingTalkAlert(secret, access_token)
        ding.send_alert(message=context)
