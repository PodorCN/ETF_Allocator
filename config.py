# Maps a display label to its Yahoo Finance symbol.
# All of these trade on the TSX (CAD) -> ".TO" suffix is added automatically.
#
# Two groups:
# - US Sectors: the BMO SPDR Select Sector Index ETFs (launched Feb 2025),
#   one per GICS sector of the S&P 500 (unhedged CAD units).
# - Global: broad ETFs covering Canada, US, developed international and
#   emerging markets so the portfolio can span the whole world.

US_SECTOR_TICKERS = {
    "ZXLE": "ZXLE.TO",  # Energy
    "ZXLF": "ZXLF.TO",  # Financials
    "ZXLV": "ZXLV.TO",  # Health Care
    "ZXLK": "ZXLK.TO",  # Information Technology
    "ZXLU": "ZXLU.TO",  # Utilities
    "ZXLI": "ZXLI.TO",  # Industrials
    "ZXLB": "ZXLB.TO",  # Materials
    "ZXLC": "ZXLC.TO",  # Communication Services
    "ZXLY": "ZXLY.TO",  # Consumer Discretionary
    "ZXLP": "ZXLP.TO",  # Consumer Staples
    "ZXLR": "ZXLR.TO",  # Real Estate
}

GLOBAL_TICKERS = {
    "ZCN": "ZCN.TO",  # Canada (S&P/TSX Composite)
    "ZSP": "ZSP.TO",  # US large cap (S&P 500)
    "ZEA": "ZEA.TO",  # Developed intl (MSCI EAFE)
    "ZEM": "ZEM.TO",  # Emerging markets (MSCI EM)
}

TICKERS = {**US_SECTOR_TICKERS, **GLOBAL_TICKERS}

# Display order -> group name each label belongs to (used by the UI).
TICKER_GROUPS = [
    ("US S&P 500 Sectors", list(US_SECTOR_TICKERS.keys())),
    ("Global Coverage", list(GLOBAL_TICKERS.keys())),
]

# Short human-readable note per ticker (shown as a hover tooltip in the UI):
# what the fund tracks / which market it proxies.
TICKER_NOTES = {
    "ZXLE": "US Energy sector — oil & gas majors (tracks XLE via BMO SPDR suite)",
    "ZXLF": "US Financials sector — banks, insurers, payments (XLF)",
    "ZXLV": "US Health Care sector — pharma & devices (XLV)",
    "ZXLK": "US Information Technology — software & semis (XLK)",
    "ZXLU": "US Utilities sector — regulated power, renewables (XLU)",
    "ZXLI": "US Industrials — aerospace, transport, machinery (XLI)",
    "ZXLB": "US Materials — chemicals, metals, mining (XLB)",
    "ZXLC": "US Communication Services — media & telecom (XLC)",
    "ZXLY": "US Consumer Discretionary — retail, autos, travel (XLY)",
    "ZXLP": "US Consumer Staples — food, beverages, household (XLP)",
    "ZXLR": "US Real Estate sector — REITs & property (XLRE)",
    "ZCN": "Canada broad market — S&P/TSX Composite (~240 names)",
    "ZSP": "US large-cap broad market — S&P 500 (500 names)",
    "ZEA": "Developed international ex-North America — MSCI EAFE (Europe, Australasia, Far East)",
    "ZEM": "Emerging markets — MSCI EM (China, India, Taiwan, Brazil...)",
}

BASE_CURRENCY = "CAD"

# Ticker (must be a key in TICKERS above) shown as the benchmark line/delta
# on the Portfolio Return chart.
BENCHMARK_TICKER = "ZSP"

# How much daily history to pull. Needs to comfortably cover the longest
# correlation lookback window plus MTD/QTD anchor dates. Note: the BMO SPDR
# sector ETFs only launched in Feb 2025, so their history caps out there -
# a 5y pull gives them everything that exists.
HISTORY_PERIOD = "5y"

# How often the dashboard re-fetches data from Yahoo Finance (ms).
REFRESH_INTERVAL_MS = 5 * 60 * 1000  # 5 minutes

# How long a fetched price DataFrame (in-memory, and the on-disk cache in
# cache/price_data.pkl) is reused before hitting Yahoo again (s). Keep this
# in sync with REFRESH_INTERVAL_MS - there's no point refreshing more often
# than the UI re-triggers, or caching longer than the UI's refresh cadence.
CACHE_TTL_SECONDS = 5 * 60

DEFAULT_CORR_LOOKBACK = 90
CORR_LOOKBACK_OPTIONS = [20, 30, 60, 90, 180, 252]

# Exponential-decay covariance estimator (RiskMetrics-style EWMA): the
# half-life controls how fast older observations' weight decays.
COV_DEFAULT_HALFLIFE = 63
COV_HALFLIFE_OPTIONS = [21, 42, 63, 126, 252]

# ---- Optimized portfolio (max Sharpe) ----

# Annualized risk-free rate used for the Sharpe ratio.
RISK_FREE_RATE = 0.02

# Trailing window (trading days) used to estimate expected returns.
OPT_LOOKBACK = 252

# EWMA half-life used for the optimizer's covariance estimate.
OPT_COV_HALFLIFE = 63

# ---- Target portfolio ----
# Max Sharpe strategy estimated on a ROLLING window that ends 2 months ago:
# data from (T - 38 months) to (T - 2 months), i.e. 36 months of returns,
# with exponential decay across observations. Recomputed on every refresh,
# so it rolls forward automatically as new data arrives.
TARGET_EST_MONTHS = 38
TARGET_SKIP_MONTHS = 2

# Decay half-life (trading days) applied within the estimation window -
# newer observations count more, older ones fade out smoothly.
TARGET_HALFLIFE = 126
