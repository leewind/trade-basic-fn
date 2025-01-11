import statsmodels.api as sm
from pykalman import KalmanFilter
import numpy as np


def get_kalman_filter_state(plus, minus):
    """
    Applies a Kalman filter to the given time series data.

    Parameters:
    plus (pd.Series or np.ndarray): The time series data for the 'plus' variable.
    minus (pd.Series or np.ndarray): The time series data for the 'minus' variable.

    Returns:
    tuple: A tuple containing:
        - state_means (np.ndarray): The estimated state means from the Kalman filter.
        - state_covs (np.ndarray): The estimated state covariances from the Kalman filter.
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
        observation_covariance=0.5,
        transition_covariance=0.000001 * np.eye(2),
    )

    state_means, state_covs = kf.filter(np.log(plus).values)
    return state_means, state_covs


def get_kalman_filter_spread(plus, minus):
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
    state_means, state_covs = get_kalman_filter_state(plus, minus)
    return np.log(plus) - np.log(minus) * state_means[:, 0] - state_means[:, 1]


def cal_half_life(spread):
    """
    Calculate the half-life of mean reversion for a given spread series.

    The half-life is the time it takes for a spread to revert halfway back to its mean.

    Parameters:
    spread (pd.Series): A pandas Series representing the spread.

    Returns:
    int: The calculated half-life of mean reversion. If the calculated half-life is less than or equal to 0, it returns 1.
    """
    spread_lag = spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = int(round(-np.log(2) / res.params[1], 0))
    if halflife <= 0:
        halflife = 1
    return halflife
