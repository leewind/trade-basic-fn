import clickhouse_connect
import pandas as pd
import datetime


def get_coin_data_by_ct(
    code,
    start_time,
    freq="1m",
    host="117.131.54.182",
    table_prefix="coin_futures_price_with_ct_",
):
    """
    Fetches cryptocurrency data from a ClickHouse database and processes it.

    Parameters:
    code (str): The cryptocurrency pair code.
    start_time (int): The start time in Unix timestamp format.
    freq (str, optional): The frequency of the data (default is "1m").
    host (str, optional): The host address of the ClickHouse server (default is "117.131.54.182").
    table_prefix (str, optional): The prefix of the table name in the database (default is "coin_futures_price_with_ct_").

    Returns:
    pandas.DataFrame: A DataFrame containing the fetched data with additional columns for returns and indexed by time.
    """
    client = clickhouse_connect.get_client(
        host=host, port="8123", password="Milkt@2021", database="coin"
    )
    sql = f"select * from {table_prefix}{freq} where pair='{code}' and stime > {start_time} order by stime asc"
    df = client.query_df(sql)
    client.close()
    df = df.drop_duplicates(subset="stime", keep="first")
    df["stime"] = pd.to_datetime(df["stime"], unit="s")
    df.set_index("stime", inplace=True)
    df.sort_index(inplace=True)
    df["returns"] = df.close.pct_change()
    return df


def aggregate_data_by_ct(df, freq="15min", base=0, mode="crypto"):
    """
    Aggregates the given DataFrame by the specified frequency.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing the data to be aggregated.
    freq (str, optional): The frequency for resampling the data. Default is "15min".
    base (int, optional): The base time in minutes for resampling. Default is 0.
    mode (str, optional): The mode of operation, either "crypto" or "ashare". Default is "crypto".

    Returns:
    pd.DataFrame: The aggregated DataFrame.

    Notes:
    - The function resamples the data based on the given frequency and aggregates it using the specified aggregation rules.
    - The aggregation rules are applied only to the columns present in the input DataFrame.
    - If the mode is "ashare", the function filters the data to include only the time between 09:30 and 15:00.
    - The function removes rows where the 'close' column is null after aggregation.
    """

    agg_dict = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "amount": "sum",
        "trade_num": "sum",
        "active_buy_volume": "sum",
        "active_buy_amount": "sum",
    }

    agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}

    base_h, base_m = base // 60, base % 60
    aggregated_df = (
        df.resample(freq, closed="left", origin=f"2020-01-01 {base_h}:{base_m}:00")
        .agg(agg_dict)
        .shift()
    )

    if mode == "ashare":
        aggregated_df = aggregated_df.between_time("09:30", "15:00")
    aggregated_df = aggregated_df[aggregated_df.close.notnull()]
    return aggregated_df


def fetch_and_normalize_coin_data(
    symbol, freq="5min", start_day_gap=30, end_day_gap=0
) -> pd.DataFrame:
    """
    Fetches and normalizes cryptocurrency data for a given symbol.
    Parameters:
    symbol (str): The symbol of the cryptocurrency to fetch data for (e.g., 'BTC').
    freq (str, optional): The frequency of the data aggregation (default is '5min').
    start_day_gap (int, optional): The number of days before today to start fetching data (default is 30).
    end_day_gap (int, optional): The number of days before today to stop fetching data (default is 0).
    Returns:
    pd.DataFrame: A DataFrame containing the normalized and aggregated cryptocurrency data with additional moving averages.
    """
    startdate = datetime.datetime.now() - datetime.timedelta(days=start_day_gap)
    enddate = datetime.datetime.now() - datetime.timedelta(days=end_day_gap)

    dforigin = get_coin_data_by_ct(
        f"{symbol}_USDT", startdate.timestamp(), freq="1m", host="117.131.54.182"
    )
    dforigin = dforigin[
        dforigin.ctime < int((enddate + datetime.timedelta(minutes=1)).timestamp())
    ]

    dfo = aggregate_data_by_ct(dforigin, freq=freq, base=0, mode="crypto").reset_index()

    max_price = dfo.high.max()
    dfo.close = dfo.close / max_price
    dfo.open = dfo.open / max_price
    dfo.high = dfo.high / max_price
    dfo.low = dfo.low / max_price

    dfo["ma10"] = dfo.close.rolling(window=10).mean()
    dfo["ma20"] = dfo.close.rolling(window=20).mean()
    dfo["ma30"] = dfo.close.rolling(window=30).mean()

    dfu = dfo[50:].copy().reset_index(drop=True)
    return dfu
