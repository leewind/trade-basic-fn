import pymysql
import configparser


class MysqlConnector:
    def connect(self, config_filename):
        config = configparser.ConfigParser()
        config.read(config_filename)

        conn = pymysql.connect(
            host=config["db"]["host"],
            port=int(config["db"]["port"]),
            user=config["db"]["user"],
            password=config["db"]["password"],
            database=config["db"]["database"],
        )

        return conn
