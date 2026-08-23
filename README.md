# ETF_Allocator

A Dash dashboard for a CAD-based asset-allocation portfolio built from the
**BMO SPDR Select Sector Index ETFs** (all 11 GICS sectors of the S&P 500,
listed on the TSX) plus broad **global coverage** ETFs:

- US Sectors: ZXLE (Energy), ZXLF (Financials), ZXLV (Health Care), ZXLK
  (Technology), ZXLU (Utilities), ZXLI (Industrials), ZXLB (Materials),
  ZXLC (Communication Services), ZXLY (Cons. Discretionary), ZXLP
  (Cons. Staples), ZXLR (Real Estate)
- Global: ZCN (Canada), ZSP (US S&P 500), ZEA (MSCI EAFE), ZEM (MSCI EM)

Single page, no tabs:
- **ETF / Index Returns** — last close, daily / MTD / QTD % return per ETF.
  All returns are computed on **total return series** (dividends reinvested,
  via Yahoo's adjusted closes).
- **Portfolio Weights** — enter a weight (%) per ETF via a number box or its
  slider (kept in sync), grouped by US sectors vs global coverage. Click the
  📌 next to a ticker to **pin** it — the "Equal Weight (unpinned)" button
  then only redistributes 100% minus the pinned total evenly across the
  *unpinned* tickers.
- **Portfolio Return** — daily / MTD / QTD return of the weighted portfolio
  (each with its delta vs the `BENCHMARK_TICKER`) and a cumulative return
  chart with a benchmark line overlaid.
- **Risk Matrix** — toggle between:
  - *Correlation*: pairwise correlation of daily returns over a selectable
    lookback window (20–252 trading days).
  - *Covariance*: annualised covariance estimated with **exponential decay**
    (RiskMetrics-style EWMA, configurable half-life) — see
    `compute_covariance` in `data_utils.py`.

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
- Delete `cache/price_data.pkl` any time to force a clean re-fetch (you must
  do this once after changing the ticker list in `config.py`).

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
- The BMO SPDR sector ETFs launched in Feb 2025, so their price history
  starts there; lookback windows reaching before that simply use whatever
  data exists.
- Portfolio return math assumes weights are held constant (i.e. rebalanced
  daily) rather than simulating buy-and-hold drift — the standard
  simplification for an interactive "what-if" allocator.
- Styling lives in `assets/style.css` (Dash auto-loads anything in
  `assets/`).
