import clickhouse_connect
import configparser


class ClickHouseConnector:
    def connect(self, config_filename, database):
        config = configparser.ConfigParser()
        config.read(config_filename)

        return clickhouse_connect.get_client(
            host=config["clickhouse"]["host"],
            username="default",
            password=config["clickhouse"]["password"],
            database=database
        )

    def read_mysql_2_pandas(self, config_filename, database, sql):
        client = self.connect(config_filename, database)
        return client.query_df(sql)
    
    def read_2_pandas(self, config_filename, database, sql):
        client = self.connect(config_filename, database)
        df = client.query_df(sql)
        client.close()

        return df
