# ETF_Allocator

A Dash dashboard for an ETF asset-allocation portfolio (CAD base currency):
ZSP, XIU, ZEB, HFIN, BANK, XEC, XCS.

Single page, no tabs:
- **ETF / Index Returns** — last close, daily / MTD / QTD % return per ETF.
- **Portfolio Weights** — enter a weight (%) per ETF via a number box or its
  slider (kept in sync). Click the 📌 next to a ticker to **pin** it — the
  "Equal Weight (unpinned)" button then only redistributes 100% minus the
  pinned total evenly across the *unpinned* tickers, leaving pinned weights
  untouched.
- **Portfolio Return** — the resulting portfolio's daily / MTD / QTD return
  (each with its delta vs the ZSP benchmark) and a cumulative return chart
  with a ZSP benchmark line overlaid. Change the benchmark via
  `BENCHMARK_TICKER` in `config.py`.
- **Correlation Matrix** — heatmap of pairwise daily-return correlation over
  a selectable lookback window (20–252 trading days).

Data comes from Yahoo Finance via `yfinance` (free tier — end-of-day data,
plus whatever intraday last-price Yahoo happens to expose; not a paid
real-time feed). The dashboard auto-refreshes every 5 minutes
(`REFRESH_INTERVAL_MS` in `config.py`).

### Caching
Price data is cached in two layers to keep load times fast and to survive
flaky/no internet:
- In-memory, for `CACHE_TTL_SECONDS` (default 5 min, matching the refresh
  interval).
- On disk at `cache/price_data.pkl`. A fresh app restart reuses this file
  instead of hitting Yahoo Finance if it's still within `CACHE_TTL_SECONDS`
  old. If a live fetch ever fails (e.g. no internet), the dashboard falls
  back to this file no matter how stale, and the status pill in the header
  turns red and says "Showing cached data as of ...".
- Delete `cache/price_data.pkl` any time to force a clean re-fetch.

## Setup

1. Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
   (check "Add python.exe to PATH" during install), then restart your
   terminal.

2. From this folder:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Run it:

   ```powershell
   python app.py
   ```

4. Open http://127.0.0.1:8050 in your browser.

## Notes / things to check after first run
- `config.py` maps each display label to its Yahoo Finance symbol; all
  current tickers use the `.TO` (TSX) suffix. If the correlation matrix or
  portfolio chart looks off for one ETF, double check its symbol resolves
  on [finance.yahoo.com](https://finance.yahoo.com) and adjust `config.py`.
- Portfolio return math assumes weights are held constant (i.e. rebalanced
  daily) rather than simulating buy-and-hold drift — the standard
  simplification for an interactive "what-if" allocator.
- Styling lives in `assets/style.css` (Dash auto-loads anything in
  `assets/`).
