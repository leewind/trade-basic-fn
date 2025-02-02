import datetime
from os.path import exists
import tushare as ts
import pandas as pd
import math
import numpy as np
from .clickhouse_connect_helper import ClickHouseConnector

TUSHARE_KEY = "32edd62d8ec424bd141e2992ffd0725c51b246e205115188d1576229"
ts.set_token(TUSHARE_KEY)
pro = ts.pro_api()


class StockBasicInfo(object):
    _instance = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls, config_name):
        if cls._instance is None:
            ck = ClickHouseConnector()

            df_fund_list = ck.read_2_pandas(
                config_name, 'quote', "select ts_code,symbol from tushare_fund_basic"
            )
            df_stock_list = ck.read_2_pandas(
                config_name, 'quote', "select ts_code,symbol from tushare_stock_basic"
            )

            cls._instance = pd.concat([df_fund_list, df_stock_list])

        return cls._instance

class StockCalendarInfo(object):
    _instance = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls, config_name):
        if cls._instance is None:
            ck = ClickHouseConnector()

            df_cal = ck.read_2_pandas(
                config_name, 'stock', "select * from milkt_stock_calendar"
            )

            cls._instance = df_cal

        return cls._instance


def check_ts_symbol(symbol, config_name="config.ini"):
    df_stock_list = StockBasicInfo.instance(config_name)
    m = df_stock_list[df_stock_list["symbol"] == symbol]

    if m is None or len(m) == 0:
        return None
    else:
        return m.iloc[0]["ts_code"]


def is_in_trading_time() -> bool:
    ct = datetime.datetime.now()
    hm = int(ct.strftime("%H%M%S"))
    if (hm >= 92950 and hm <= 113000) or (hm >= 125950 and hm <= 150003):
        return True

    return False


def is_after_trading_time() -> bool:
    ct = datetime.datetime.now()
    if ct.hour > 14:
        return True

    return False


def is_after_sys_working_time() -> bool:
    ct = datetime.datetime.now()
    if ct.hour > 15:
        return True

    if ct.hour > 14 and ct.minute > 5:
        return True

    return False


def read_from_cache(dt) -> pd.DataFrame:
    filename = "trading_date.csv"
    if not exists(filename):
        # df = pro.trade_cal(exchange="", start_date=dt, end_date=dt)
        # df.to_csv(filename, index=False)
        
        return StockCalendarInfo.instance("config.ini").to_csv(filename, index=False)
        # return df

    df = pd.read_csv(filename)
    if len(df[df["cal_date"] == dt]) == 0:
        # df = pro.trade_cal(exchange="", start_date=dt, end_date=dt)
        # df.to_csv(filename, index=False)
        StockCalendarInfo.instance("config.ini").to_csv(filename, index=False)

    df['cal_date'] = df['cal_date'].astype(str)
    return df


def read_debt_list_from_cache(dt) -> pd.DataFrame:
    filename = "debt_date.csv"
    if not exists(filename):
        df = pro.margin_target(mg_type="B")
        df["dt"] = dt
        df.to_csv(filename, index=False)
        return df

    df = pd.read_csv(filename, dtype={"dt": str})
    if len(df[df["dt"] == dt]) == 0:
        df = pro.margin_target(mg_type="B")
        df["dt"] = dt
        df.to_csv(filename, index=False)

    return df


def is_debt_buy(symbol) -> bool:
    ct = datetime.datetime.now()
    dt = ct.strftime("%Y%m%d")

    df = read_debt_list_from_cache(dt)
    return len(df[df["ts_code"] == symbol]) > 0


def is_in_trading_day() -> bool:
    ct = datetime.datetime.now()
    dt = ct.strftime("%Y%m%d")

    df = read_from_cache(dt)

    if df is None or len(df) == 0:
        return False

    print(df)
    print(dt)
    print(df[df["cal_date"] == dt])
    return df[df["cal_date"] == dt].iloc[0]["is_open"] > 0


def get_1m_raw_pressure_and_support(df, gap=0.005):
    p2 = df.groupby("close").agg({"volume": "sum"}).reset_index()
    p2["datetime"] = p2["volume"]
    p2["last"] = p2["close"]

    data = []
    for index, row in p2.sort_values("datetime", ascending=False).iterrows():
        price = row["last"]
        count = abs(row["datetime"])

        is_not_in_price_list = True
        for index in range(0, len(data)):
            d = data[index]
            if price <= d["price"] * (1 + gap) and price >= d["price"] * (1 - gap):
                is_not_in_price_list = False
                data[index]["datetime"] = data[index]["datetime"] + count
                break

        if is_not_in_price_list:
            data.append({"price": price, "datetime": count})

    return data


def compute_volatility(contract):
    # 包含多少天的标的合约价格
    days = len(contract)

    # 获取每日收盘价（或者结算价）并存入数组
    prices = contract["close"].values.tolist()

    # 对价格取自然对数
    ln_prices = [np.log(x) for x in prices]

    # 以下表示取对数价格的差，并存在diffPriceArray数组中，   //我们忽略了边界条件，实际  得到数组长度为nDays-1
    diff_prices = []
    for i in range(days):
        diff_prices.append(ln_prices[i] - ln_prices[i - 1])

    # 计算波动率
    sigma = np.std(diff_prices) * math.sqrt(250 / days)
    return sigma


def get_code_volatility(ts_code, end_date, length):
    start_date = "20210101"

    if ("1" in ts_code and ts_code.index("1") == 0) or (
        "5" in ts_code and ts_code.index("5") == 0
    ):
        df = pro.fund_daily(
            ts_code=ts_code, adj="qfq", start_date=start_date, end_date=end_date
        )
    else:
        df = ts.pro_bar(
            ts_code=ts_code, adj="qfq", start_date=start_date, end_date=end_date
        )
    df = df.sort_values("trade_date", ascending=True).reset_index()

    days_dates = df[df["trade_date"] > "20210201"]["trade_date"].values
    targets = days_dates[-length:]

    index = df[df["trade_date"].isin(targets)].iloc[0].name
    start_index = df.iloc[index - 10].name
    end_index = df.iloc[index - 1].name

    if end_index < start_index:
        return None

    tmp = df[start_index:end_index].copy()

    if tmp is None:
        return None

    prices = tmp.reset_index()

    value = round(compute_volatility(prices) * 0.1, 4)
    return value
