from manager_selection.config import MANAGERS

# Strategy universe. Label -> TSX symbol we trade (all CAD, ".TO").
UNIVERSE = {
    # BMO SPDR Select Sector ETFs (S&P 500 sectors, CAD unhedged)
    "ZXLC": "ZXLC.TO",  # Communication Services
    "ZXLY": "ZXLY.TO",  # Consumer Discretionary
    "ZXLP": "ZXLP.TO",  # Consumer Staples
    "ZXLE": "ZXLE.TO",  # Energy
    "ZXLF": "ZXLF.TO",  # Financials
    "ZXLV": "ZXLV.TO",  # Health Care
    "ZXLI": "ZXLI.TO",  # Industrials
    "ZXLB": "ZXLB.TO",  # Materials
    "ZXLR": "ZXLR.TO",  # Real Estate
    "ZXLK": "ZXLK.TO",  # Technology
    "ZXLU": "ZXLU.TO",  # Utilities
    "HUG": "HUG.TO",    # Global X Gold ETF
    "XEC": "XEC.TO",    # iShares Core MSCI Emerging Markets IMI
    "XEU": "XEU.TO",    # iShares MSCI Europe IMI
    # Fixed income
    "XHY": "XHY.TO",    # iShares US High Yield Bond (CAD-hedged)
    "XIG": "XIG.TO",    # iShares US IG Corporate Bond (CAD-hedged)
    "XHB": "XHB.TO",    # iShares Canadian HYBrid Corporate Bond (no pure CA HY ETF exists)
    "XCB": "XCB.TO",    # iShares Core Canadian Corporate Bond (IG)
}

# The BMO sector ETFs only started trading in Feb 2025, too short for
# 12-month signals. Compute signals on the US SPDR originals (same index,
# history back to 1998) and trade the BMO versions.
SIGNAL_PROXY = {
    "ZXLC": "XLC",
    "ZXLY": "XLY",
    "ZXLP": "XLP",
    "ZXLE": "XLE",
    "ZXLF": "XLF",
    "ZXLV": "XLV",
    "ZXLI": "XLI",
    "ZXLB": "XLB",
    "ZXLR": "XLRE",
    "ZXLK": "XLK",
    "ZXLU": "XLU",
    "XHY": "HYG",
    "XIG": "LQD",
}

# Traded ETFs that are hedged to CAD: their USD proxy is used as-is,
# without converting to CAD.
CAD_HEDGED = {"XHY", "XIG"}

BASE_CURRENCY = "CAD"

# ---- ETF Constructor page (pages/constructor.py, data_utils.fetch_price_data) ----
# Benchmark line / delta on the Portfolio Return chart (shown, not allocated to).
BENCHMARK_TICKER = "ZSP"

# Label -> Yahoo symbol of what we actually hold: UNIVERSE with each manager
# (manager_selection/config.py) in place of the slot it replaces, plus the benchmark.
HOLDINGS = {
    (MANAGERS[label]["symbol"].split(".")[0] if label in MANAGERS else label):
        (MANAGERS[label]["symbol"] if label in MANAGERS else symbol)
    for label, symbol in UNIVERSE.items()
}
TICKERS = {**HOLDINGS, BENCHMARK_TICKER: "ZSP.TO"}

# How much daily history to pull. Needs to comfortably cover the longest
# correlation lookback window plus MTD/QTD anchor dates.
HISTORY_PERIOD = "1y"

# How often the dashboard re-fetches data from Yahoo Finance (ms).
REFRESH_INTERVAL_MS = 5 * 60 * 1000  # 5 minutes

# How long a fetched price DataFrame (in-memory, and the on-disk cache in
# cache/price_data.pkl) is reused before hitting Yahoo again (s). Keep this
# in sync with REFRESH_INTERVAL_MS - there's no point refreshing more often
# than the UI re-triggers, or caching longer than the UI's refresh cadence.
CACHE_TTL_SECONDS = 5 * 60

DEFAULT_CORR_LOOKBACK = 90
CORR_LOOKBACK_OPTIONS = [20, 30, 60, 90, 180, 252]
