import statsmodels.api as sm
from pykalman import KalmanFilter
import numpy as np


class AlgoKalmanFilterProcessor:
    """
    AlgoKalmanFilterProcessor is a class that provides methods to process time series data using a Kalman filter.
    Methods:
        get_kalman_filter_state(plus, minus, observation_convariance=0.5):
                observation_convariance (float, optional): The observation covariance. Default is 0.5.
        get_kalman_filter_spread(plus, minus, observation_convariance=0.5):
                observation_convariance (float, optional): The observation covariance. Default is 0.5.
        cal_half_life(spread, seed=2):
        process_kf_df(df, plus, minus, seed=2, fast=10, slow=30):
                fast (int, optional): The window size for the fast rolling mean of the z-score. Default is 10.
                slow (int, optional): The window size for the slow rolling mean of the z-score. Default is 30.
                    - 'kf_zscore_ma10': The rolling mean of the original z-score with a window of 10.
                    - 'kf_zscore_ma30': The rolling mean of the original z-score with a window of 30.
    """

    @staticmethod
    def get_kalman_filter_state(plus, minus, observation_convariance=0.5):
        """
        Applies a Kalman filter to the given time series data.

        Parameters:
        plus (pd.Series or np.ndarray): The time series data for the 'plus' variable.
        minus (pd.Series or np.ndarray): The time series data for the 'minus' variable.

        Returns:
        tuple: A tuple containing:
            - state_means (np.ndarray): The estimated state means from the Kalman filter.
            - state_covs (np.ndarray): The estimated state covariances from the Kalman filter.


        kf = KalmanFilter(
            transition_matrices=[[1, delta_t], [0, 1]], #系统矩阵
            transition_offsets=[0, 0],#类似于输入矩阵与输入的乘积，注意格式，
            #如有三个状态量就写成[0, 0, 0]
            transition_covariance=[[0, 0], [0, 10]],#模型协方差
            observation_matrices=[1, 0],#观测矩阵，仅有一个观测量
            observation_offsets=[0],#类似，因为只有一个观测量
            observation_covariance=[10],#观测协方差
            initial_state_mean = [0, 0],#以下两项用于定义初始的状态
            initial_state_covariance = [[1, 0], [0, 1]]
            em_vars: List[str] = ['transition_matrices', 'observation_matrices',
                                'transition_offsets', 'observation_offsets',
                                'transition_covariance', 'observation_covariance',
                                'initial_state_mean','initial_state_covariance'],
            #em_vars用于定义应用em算法时，对那些参数进行训练
            #如:em_vars=['transition_covariance','observation_covariance']
            #代表仅对这两个参数进行训练
        )
        """
        obs_mat = sm.add_constant(np.log(minus).values, prepend=False)[:, np.newaxis]
        trans_cov = 1e-5 / (1 - 1e-5) * np.eye(2)

        kf = KalmanFilter(
            n_dim_obs=1,
            n_dim_state=2,
            initial_state_mean=np.ones(2),
            initial_state_covariance=np.ones((2, 2)),
            transition_matrices=np.eye(2),
            observation_matrices=obs_mat,
            observation_covariance=observation_convariance,
            transition_covariance=0.000001 * np.eye(2),
        )

        state_means, state_covs = kf.filter(np.log(plus).values)
        return state_means, state_covs

    @staticmethod
    def get_kalman_filter_spread(plus, minus, observation_convariance=0.5):
        """
        Calculate the spread using the Kalman filter.

        This function computes the spread between two time series using the Kalman filter.
        It first obtains the state means and covariances from the Kalman filter, then
        calculates the spread as the difference between the logarithms of the 'plus' and
        'minus' series, adjusted by the state means.

        Args:
            plus (np.ndarray): The first time series (numerator).
            minus (np.ndarray): The second time series (denominator).

        Returns:
            np.ndarray: The calculated spread.
        """
        state_means, state_covs = AlgoKalmanFilterProcessor.get_kalman_filter_state(
            plus, minus, observation_convariance=observation_convariance
        )
        return np.log(plus) - np.log(minus) * state_means[:, 0] - state_means[:, 1]

    @staticmethod
    def cal_half_life(spread, seed=2):
        """
        Calculate the half-life of a mean-reverting time series.

        The half-life is the time it takes for a time series to revert halfway back to its mean.
        This function uses an Ordinary Least Squares (OLS) regression to estimate the half-life.

        Parameters:
        spread (pd.Series): The time series data for which the half-life is to be calculated.
        seed (int, optional): The base of the logarithm used in the calculation. Default is 2.

        Returns:
        int: The calculated half-life of the time series. If the calculated half-life is less than or equal to 0, it returns 1.
        """
        spread_lag = spread.shift(1)
        spread_lag.iloc[0] = spread_lag.iloc[1]
        spread_ret = spread - spread_lag
        spread_ret.iloc[0] = spread_ret.iloc[1]
        spread_lag2 = sm.add_constant(spread_lag)
        model = sm.OLS(spread_ret, spread_lag2)
        res = model.fit()
        halflife = int(round(-np.log(seed) / res.params[1], 0))
        if halflife <= 0:
            halflife = 1
        return halflife

    @staticmethod
    def process_kf_df(df, plus, minus, seed=2, fast=10, slow=30):
        """
        Processes a DataFrame using a Kalman filter to compute spreads and z-scores.
        Args:
            df (pd.DataFrame): The input DataFrame containing the data to be processed.
            plus (str): The column name in the DataFrame representing the 'plus' series.
            minus (str): The column name in the DataFrame representing the 'minus' series.
            seed (int, optional): A seed value used to determine the rolling window size for z-score calculation. Default is 2.
        Returns:
            pd.DataFrame: The processed DataFrame with additional columns:
                - 'kl_spread': The Kalman filter spread between the 'plus' and 'minus' series.
                - 'kf_zscore_origin': The original z-score of the Kalman filter spread.
                - 'kf_zscore': The rolling mean of the original z-score with a window of 10.
                - 'kf_zscore_ma5': The rolling mean of the original z-score with a window of 30.
        """
        df['kl_spread'] = AlgoKalmanFilterProcessor.get_kalman_filter_spread(plus, minus, 0.5)

        # @Note 不再计算半衰期，直接传入半衰期
        df['kf_zscore_origin'] = df['kl_spread'].rolling(int(seed * 2) ).apply(lambda item: (item.iloc[-1] - item.mean()) / item.std())

        df[f'kf_zscore_ma{fast}'] = df['kf_zscore_origin'].rolling(window=fast).mean()
        df[f'kf_zscore_ma{slow}'] = df['kf_zscore_origin'].rolling(window=slow).mean()

        return df