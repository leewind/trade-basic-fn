import clickhouse_connect
import configparser


class ClickHouseConnector:
    def connect(self, config_filename):
        config = configparser.ConfigParser()
        config.read(config_filename)

        return clickhouse_connect.get_client(
            host=config["clickhouse"]["host"],
            username="default",
            password=config["clickhouse"]["password"],
        )

    def pandas_save_2_mysql(self, config_filename, sql):
        client = self.connect(config_filename)
        return client.query_df(sql)
