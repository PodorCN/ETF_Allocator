import pandas as pd
import yfinance as yf

MAX_YEARS = 20


def get_daily_prices(ticker: str, years: int = MAX_YEARS) -> pd.DataFrame:
    """Adjusted daily OHLCV for one ticker from Yahoo Finance.

    Covers the last `years` years (capped at 20), or less if the ticker
    has a shorter history. Prices are adjusted for splits and dividends.
    """
    years = min(years, MAX_YEARS)
    start = pd.Timestamp.today().normalize() - pd.DateOffset(years=years)

    df = yf.Ticker(ticker).history(start=start, interval="1d", auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned from Yahoo Finance for {ticker!r}")

    df.index = df.index.tz_localize(None)
    df.index.name = "Date"
    return df[["Open", "High", "Low", "Close", "Volume"]]


def get_adj_close(ticker: str, years: int = MAX_YEARS) -> pd.Series:
    """Adjusted daily close for one ticker, named after the ticker."""
    return get_daily_prices(ticker, years)["Close"].rename(ticker)


if __name__ == "__main__":
    import sys

    df = get_daily_prices(sys.argv[1] if len(sys.argv) > 1 else "SPY")
    print(df.head(), df.tail(), f"{len(df)} rows", sep="\n")
