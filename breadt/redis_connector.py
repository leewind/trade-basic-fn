import redis
import configparser


class RedisConnector:
    def connect(self, config_filename):
        config = configparser.ConfigParser()
        config.read(config_filename)

        conn = redis.Redis(
            host=config["redis"]["host"],
            port=config["redis"]["port"],
            decode_responses=True,
        )

        return conn
