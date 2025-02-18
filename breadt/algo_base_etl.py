import numpy as np
import pandas as pd


class AlgorithmBaseETL:
    """
    AlgorithmBaseETL class provides methods for performing ETL (Extract, Transform, Load) operations on financial data.
    Methods:
        cal_volatility(df: pd.DataFrame, window: int = 36) -> pd.DataFrame:
    """

    @staticmethod
    def cal_volatility(df: pd.DataFrame, window: int = 36) -> pd.DataFrame:
        """
        Calculate the rolling volatility of a given DataFrame's 'close' column.

        Parameters:
        df (pd.DataFrame): DataFrame containing the 'close' prices.
        window (int): The rolling window size to calculate the standard deviation. Default is 36.

        Returns:
        pd.DataFrame: DataFrame with an additional 'volatility' column representing the rolling volatility.
        """
        returns = np.log(df["close"] / df["close"].shift(1))
        returns.fillna(0, inplace=True)
        volatility = returns.rolling(window=window).std() * np.sqrt(6)
        df["volatility"] = volatility
        return df

    @staticmethod
    def rma(cps, days=8):
        """
        Calculate the Running Moving Average (RMA) of a list of closing prices.
        Args:
            cps (list): A list of closing prices.
            days (int, optional): The number of days to calculate the RMA over. Default is 8.
        Returns:
            list: A list containing the RMA values for each closing price in cps.
        """
        emas = [0 for i in range(len(cps))]  # 创造一个和cps一样大小的集合
        for i, cp in enumerate(cps):
            if i == 0:
                emas[i] = cp
            else:
                emas[i] = ((days - 1) * emas[i - 1] + 2 * cp) / (days + 1)

        emas = [v for v in emas]
        return emas

    @staticmethod
    def get_adx_resolution(close, high, low, length=8, smoothing=8):
        """
        Calculate the Average Directional Index (ADX) resolution along with the 
        positive and negative directional indicators.
        Parameters:
        close (np.ndarray): Array of closing prices.
        high (np.ndarray): Array of high prices.
        low (np.ndarray): Array of low prices.
        length (int, optional): The period length for the ADX calculation. Default is 8.
        smoothing (int, optional): The smoothing period for the ADX calculation. Default is 8.
        Returns:
        tuple: A tuple containing:
            - signal (np.ndarray): The ADX signal.
            - sec_plus (np.ndarray): The positive directional indicator.
            - sec_minus (np.ndarray): The negative directional indicator.
        """
        tr = np.max([high - low, high - close, close - low], axis=0)[1:]

        up = np.diff(high)
        down = -np.diff(low)
        true_range = AlgorithmBaseETL.rma(tr, length)

        plus = np.nan_to_num(
            100 * np.divide(AlgorithmBaseETL.rma(np.where(up > down, up, 0), length), true_range)
        )
        minus = np.nan_to_num(
            100 * np.divide(AlgorithmBaseETL.rma(np.where(down > up, down, 0), length), true_range)
        )

        sec_plus = plus
        sec_minus = minus
        sec_sum = sec_plus + sec_minus

        signal = np.multiply(
            AlgorithmBaseETL.rma(
                np.abs(sec_plus - sec_minus) / (np.where(sec_sum == 0, 1, sec_sum)),
                smoothing,
            ),
            100,
        )

        signal = np.pad(signal, (1, 0), mode="constant", constant_values=0)
        sec_plus = np.pad(sec_plus, (1, 0), mode="constant", constant_values=0)
        sec_minus = np.pad(sec_minus, (1, 0), mode="constant", constant_values=0)

        return signal, sec_plus, sec_minus

    @staticmethod
    def get_adx_trend(adx, threshold, plus, minus):
        """
        Determines the trend based on the Average Directional Index (ADX) and 
        the Plus and Minus Directional Indicators.
        Parameters:
        adx (list of float): List of ADX values.
        threshold (float): Threshold value to determine if the ADX indicates a trend.
        plus (list of float): List of Plus Directional Indicator values.
        minus (list of float): List of Minus Directional Indicator values.
        Returns:
        list of int: List indicating the trend for each ADX value:
                     1 for an uptrend,
                     -1 for a downtrend,
                     0 for no trend.
        """
        emas = [0 for i in range(len(adx))]

        for i, adx_value in enumerate(adx):
            if adx[i] > threshold:
                if plus[i] - minus[i] > 0:
                    emas[i] = 1
                elif minus[i] - plus[i] > 0:
                    emas[i] = -1
                else:
                    emas[i] = 0

        return emas

    @staticmethod
    def get_adx_trend_idx(close, high, low, adx_trend_threshold=25, length=8, smoothing=8):
        """
        Calculate the ADX trend index for given price data.
        Parameters:
        close (list or np.array): List or array of closing prices.
        high (list or np.array): List or array of high prices.
        low (list or np.array): List or array of low prices.
        adx_trend_threshold (int, optional): Threshold value for ADX trend. Default is 25.
        length (int, optional): Length of the period for ADX calculation. Default is 8.
        smoothing (int, optional): Smoothing factor for ADX calculation. Default is 8.
        Returns:
        list: A list containing the ADX trend index values, with an initial value of 0.
        """
        adx_signal, adx_plus, adx_minus = AlgorithmBaseETL.get_adx_resolution(
            close, high, low, length=length, smoothing=smoothing
        )
        adx_trend = AlgorithmBaseETL.get_adx_trend(adx_signal, adx_trend_threshold, adx_plus, adx_minus)
        return adx_trend

    @staticmethod
    def get_adx_trend_idx_rising(close, high, low, adx_trend_threshold=25, length=8, smoothing=8, rolling_length=3):
        """
        Calculate the ADX trend index rising values.
        This function computes the ADX (Average Directional Index) trend index rising values
        based on the provided close, high, and low price data. It uses the ADX resolution
        to determine the ADX signal, ADX plus, and ADX minus values, and then calculates
        the ADX rising values by subtracting the rolling mean of the ADX signal.
        Parameters:
        close (pd.Series): Series of closing prices.
        high (pd.Series): Series of high prices.
        low (pd.Series): Series of low prices.
        adx_trend_threshold (int, optional): Threshold value for ADX trend. Default is 25.
        length (int, optional): Length of the period for ADX calculation. Default is 8.
        smoothing (int, optional): Smoothing factor for ADX calculation. Default is 8.
        rolling_length (int, optional): The window length for the rolling mean. Default is 3.
        Returns:
        pd.Series: Series containing the ADX rising values.
        """
        adx_signal, adx_plus, adx_minus = AlgorithmBaseETL.get_adx_resolution(
            close, high, low, length=length, smoothing=smoothing
        )
        f = pd.DataFrame({"adx": [0] + list(adx_signal)})
        f["adx_rising"] = f["adx"] - f["adx"].rolling(rolling_length).mean()

        return f["adx_rising"]


    @staticmethod
    def get_di_rising(di_gap, rolling_length=3):
        """
        Calculate the difference between the current di_gap and its rolling mean.
        Args:
            di_gap (pd.Series): A pandas Series representing the di_gap values.
            rolling_length (int, optional): The window length for the rolling mean. Default is 3.
        Returns:
            pd.Series: A pandas Series representing the difference between the di_gap and its rolling mean.
        """
        return di_gap - di_gap.rolling(rolling_length).mean() 