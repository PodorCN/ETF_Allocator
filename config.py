# Maps a display label to its Yahoo Finance symbol.
# All of these trade on the TSX (CAD) -> ".TO" suffix.
# Edit this if a symbol doesn't resolve for your account/region.
TICKERS = {
    "ZSP": "ZSP.TO",
    "XIU": "XIU.TO",
    "ZEB": "ZEB.TO",
    "HFIN": "HFIN.TO",
    "BANK": "BANK.TO",
    "XEC": "XEC.TO",
    "XCS": "XCS.TO",
}

BASE_CURRENCY = "CAD"

# Ticker (must be a key in TICKERS above) shown as the benchmark line/delta
# on the Portfolio Return chart.
BENCHMARK_TICKER = "ZSP"

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
