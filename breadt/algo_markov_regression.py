from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
import numpy as np
import pandas as pd


def markov_regression(t, freq="2h", k_regimes=3):
    """
    Perform Markov Regression on the given time series data.

    Parameters:
    t (pd.Series or pd.DataFrame): The time series data to be analyzed.
    freq (str, optional): The frequency of the time series data. Default is "2h".
    k_regimes (int, optional): The number of regimes to be used in the Markov Regression. Default is 3.

    Returns:
    pd.Series: A series with the reindexed regimes based on the input time series index.
    MarkovRegressionResults: The fitted Markov Regression model results.
    """
    mr = MarkovRegression(t.dropna(), k_regimes=k_regimes, freq=freq)
    mr_fitted = mr.fit()
    #   scaling so that the middle tier of the regime acts as decay if k_regimes = 3; add stuff together to make prob function that will act as indicator for regimes
    scaling = [0, 0.7, 1] if k_regimes == 3 else range(k_regimes)

    regimes = (
        (mr_fitted.smoothed_marginal_probabilities)
        .apply(lambda x: x * scaling, axis=1)
        .apply(np.sum, axis=1)
    )

    return regimes.reindex(t.index), mr_fitted


def get_pval_rolling_window(pval, stime, regime=2, rolling_window=36):
    """
    Applies a Markov switching model to p-values with a rolling window smoothing.

    Parameters:
    pval (array-like): Array of p-values to be transformed and analyzed.
    stime (array-like): Array of corresponding time indices for the p-values.
    regime (int, optional): Number of regimes for the Markov switching model. Default is 2.
    rolling_window (int, optional): Window size for the rolling mean smoothing. Default is 36.

    Returns:
    pd.Series: A pandas Series with the smoothed regimes, indexed by the original time indices.
    """

    m = pd.DataFrame(data={"pval": pval}, index=stime)

    #  applies a transformation to the p-value to make it more useful for the markov switching model
    pv = (m["pval"] + 0.6) ** 2

    #  does first round of markov switching model fitting;
    #  either 2 regimes or 3. 3 is for the middle 'high variance but nothing's really happening' tier,
    regimes, mr_model = markov_regression(pv, regime)

    #   applies rolling mean smoothing and runs it through a second regime fitting, this time with only two regimes
    ms = regimes.rolling(rolling_window).mean()
    smoothed_regimes, smoothed_mr_model = markov_regression(ms.dropna(), regime)

    smoothed_regimes_lag_removed = pd.Series(
        data=smoothed_regimes.values,
        index=smoothed_regimes.index,
    )

    return smoothed_regimes_lag_removed
