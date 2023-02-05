import pymysql
import configparser
from sqlalchemy import create_engine
import urllib.parse
import pandas as pd


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

    def create(self, config_filename):
        config = configparser.ConfigParser()
        config.read(config_filename)

        # @refer https://docs.sqlalchemy.org/en/20/core/engines.html
        engine = create_engine(
            "mysql+pymysql://{}:{}@{}:{}/{}".format(
                config["db"]["user"],
                urllib.parse.quote_plus(config["db"]["password"]),
                config["db"]["host"],
                config["db"]["port"],
                config["db"]["database"],
            ),
            pool_recycle=3600,
        )
        conn = engine.connect()
        return conn

    def pandas_save_2_mysql(self, config_filename, df, tb_name):
        df.to_sql(con=self.create(config_filename), name=tb_name, if_exists="replace")

    def read_mysql_2_pandas(self, config_filename, sql):
        return pd.read_sql(con=self.create(config_filename), sql=sql)
