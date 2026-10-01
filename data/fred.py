import pandas as pd

# FRED series via the public CSV endpoint (no API key).
# FRED serves the latest vintage, so only use series that are not revised
# (market data) or barely revised; see research_notes/signal_search_protocol.md.

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"


def get_fred(series: str, lag_days: int = 0) -> pd.Series:
    """One FRED series, dated by when it was published: each observation is moved
    `lag_days` calendar days later, so a signal only sees it once it is out."""
    df = pd.read_csv(URL.format(series), index_col=0, parse_dates=True, na_values=".")
    s = df.iloc[:, 0].dropna().rename(series)
    s.index = s.index + pd.Timedelta(days=lag_days)
    return s


if __name__ == "__main__":
    import sys
    print(get_fred(sys.argv[1] if len(sys.argv) > 1 else "BAA10Y").tail())
