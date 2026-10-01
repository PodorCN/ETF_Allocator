import yfinance as yf

# Yahoo sector name -> GICS sector
_YAHOO_SECTORS = {
    "communication_services": "Communication Services",
    "consumer_cyclical": "Consumer Discretionary",
    "consumer_defensive": "Consumer Staples",
    "energy": "Energy",
    "financial_services": "Financials",
    "healthcare": "Health Care",
    "industrials": "Industrials",
    "basic_materials": "Materials",
    "realestate": "Real Estate",
    "technology": "Information Technology",
    "utilities": "Utilities",
}


def get_sp500_sector_weights() -> dict[str, float]:
    """Current S&P 500 weight of each GICS sector (sums to 1), from SPY's holdings on Yahoo.

    Yahoo only has today's weights, no history.
    """
    raw = yf.Ticker("SPY").funds_data.sector_weightings
    weights = {_YAHOO_SECTORS[k]: v for k, v in raw.items()}
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}
