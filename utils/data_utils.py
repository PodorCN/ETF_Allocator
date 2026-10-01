import pandas as pd


def normalize_signal(
    signal: pd.Series | pd.DataFrame,
    window: int | None = None,
    min_periods: int = 20,
    cap: float = 2.0,
    center: bool = True,
) -> pd.Series | pd.DataFrame:
    """Z-score a signal against its own history and cap at +/- `cap` std.

    Works on a Series or a DataFrame (each column normalized separately).
    window=None uses an expanding window, an int uses a rolling window;
    either way only past data is used, so there is no lookahead.
    center=False only divides by the std, keeping the sign of the raw signal
    (use for signals where the sign itself matters, e.g. time-series momentum).
    """
    roll = signal.expanding(min_periods) if window is None else signal.rolling(window, min_periods)
    z = (signal - roll.mean() if center else signal) / roll.std()
    return z.clip(-cap, cap)


def cross_sectional_zscore(signal: pd.DataFrame, cap: float = 2.0, min_count: int = 3) -> pd.DataFrame:
    """Z-score each date across assets (columns) and cap at +/- `cap` std.

    Dates with fewer than `min_count` assets with data are left NaN.
    """
    z = signal.sub(signal.mean(axis=1), axis=0).div(signal.std(axis=1), axis=0)
    z.loc[signal.count(axis=1) < min_count] = float("nan")
    return z.clip(-cap, cap)
