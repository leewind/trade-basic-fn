import statsmodels.api as sm
from pykalman import KalmanFilter
import numpy as np


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
    state_means, state_covs = get_kalman_filter_state(
        plus, minus, observation_convariance=observation_convariance
    )
    return np.log(plus) - np.log(minus) * state_means[:, 0] - state_means[:, 1]


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
