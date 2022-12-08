import configparser
import pika


class RabbitMQConnector:
    def __init__(self, config_filename) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(config_filename)
        self.connection = None

    def _connect(self, heartbeat=3):
        credentials = pika.PlainCredentials(
            self.config["mq"]["user"], self.config["mq"]["password"]
        )

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config["mq"]["host"],
                credentials=credentials,
                virtual_host=self.config["mq"]["vhost"],
                heartbeat=0,
            )
        )
        channel = connection.channel()
        return connection, channel

    def send_message(self, exchange_name, routing_key, context, heartbeat=10) -> None:
        self.connection, channel = self._connect(heartbeat)
        channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=context
        )

        self.connection.close()

    def start_consume(self, queue_name, callback, heartbeat=10):
        """
        callback具体返回的参数, 可以参考这个example
        def callback(ch, method, properties, body):
            print(" [x] %r:%r" % (method.routing_key, body))
        """
        self.connection, channel = self._connect(heartbeat)
        channel.basic_consume(
            queue=queue_name, on_message_callback=callback, auto_ack=True
        )

        channel.start_consuming()
