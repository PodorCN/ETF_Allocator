# Portfolio construction config. Import as `port_con.config` (not `config`,
# which is the top-level dashboard/universe config).

from saa.signals import bond_term_spread, equity_value
from sector_rotation.macro import rate_sensitivity
from sector_rotation.low_risk import low_beta
from sector_rotation.momentum import ma_energy, mom_12_1, mom_vol_adj, residual_mom
from sector_rotation.sentiment import high_52w
from sector_rotation.value import long_term_reversal
from taa.signals import bond_tsmom, equity_credit_appetite

# ---- Assets in each sleeve (UNIVERSE labels) ----
# Equity = the 11 S&P 500 sectors: GICS sector -> ETF.
SP500_SECTORS = {
    "Communication Services": "ZXLC",
    "Consumer Discretionary": "ZXLY",
    "Consumer Staples": "ZXLP",
    "Energy": "ZXLE",
    "Financials": "ZXLF",
    "Health Care": "ZXLV",
    "Industrials": "ZXLI",
    "Materials": "ZXLB",
    "Real Estate": "ZXLR",
    "Information Technology": "ZXLK",
    "Utilities": "ZXLU",
}
EQUITY = list(SP500_SECTORS.values())
BONDS = ["XHY", "XIG", "XHB", "XCB"]
ALTERNATIVE = ["HUG", "XEC", "XEU"]
SLEEVES = {"equity": EQUITY, "fixed_income": BONDS, "alternative": ALTERNATIVE}

# ---- Baseline (port_con.portfolio.get_baseline) ----
# Sleeve weights. Inside equity: S&P 500 sector weights; inside the other
# sleeves: equal weight.
BASELINE_WEIGHTS = {"equity": 0.70, "fixed_income": 0.20, "alternative": 0.10}

# Legs for equity_credit_appetite.
HY = "XHY"
IG = "XIG"

# Passed to utils.data_utils.normalize_signal: None = expanding window.
NORMALIZE_WINDOW = None

# ---- Signals ----
# Each signal says:
#   "func":   the signal function
#   "data":   {function argument: data name in data/registry.py}
#   "weight": weight inside its layer (should sum to 1 per layer)
# L1 also has:
#   "side":   asset a high value favours; "equity" adds to the score,
#             "bond" subtracts (score > 0 = tilt to equity)
#   "center": optional, False = don't demean when normalizing (sign matters)
# L2 also has:
#   "compare": "cross" = z-score across assets each date, "own" = vs own history

# Layer switches. Off = that layer's values are 0, so the portfolio is the
# baseline (plus managers); the signals are still computed for the research pages.
# Search results for these layers: research_notes/signal_search_protocol.md.
L1_ON = True
L2_ON = True

L1_SIGNALS = {
    "saa": {
        "equity_value": {
            "func": equity_value,
            "data": {"equity": "equity_basket"},
            "weight": 0.5, "side": "equity",
        },
        "bond_term_spread": {
            "func": bond_term_spread,
            "data": {"ten_year": "us10y", "three_month": "us3m"},
            "weight": 0.5, "side": "bond",
        },
    },
    "taa": {
        "equity_credit_appetite": {
            "func": equity_credit_appetite,
            "data": {"hy": "hy", "ig": "ig"},
            "weight": 0.5, "side": "equity",
        },
        "bond_tsmom": {
            "func": bond_tsmom,
            "data": {"bonds": "bond_basket"},
            "weight": 0.5, "side": "bond", "center": False,
        },
    },
}

L2_SIGNALS = {
    "momentum": {
        "func": mom_12_1,
        "data": {"prices": "equity_prices"},
        "weight": 0.25, "compare": "cross",
    },
    "value": {
        "func": long_term_reversal,
        "data": {"prices": "equity_prices"},
        "weight": 0.25, "compare": "own",
    },
    # Weight 0 since 2026-09-30 (IC turned negative after 2016); kept for the
    # research pages. Its 0.25 is split equally over the four signals below it,
    # the best L2 candidates of research_notes/signal_search_protocol.md (none
    # passed the search's thresholds).
    "sentiment": {
        "func": high_52w,
        "data": {"prices": "equity_prices"},
        "weight": 0.0, "compare": "cross",
    },
    "macro": {
        "func": rate_sensitivity,
        "data": {"prices": "equity_prices", "ten_year": "us10y"},
        "weight": 0.25, "compare": "cross",
    },
    "risk_adj_momentum": {
        "func": mom_vol_adj,
        "data": {"prices": "equity_prices"},
        "weight": 0.0625, "compare": "cross",
    },
    "residual_momentum": {
        "func": residual_mom,
        "data": {"prices": "equity_prices", "equity": "equity_basket"},
        "weight": 0.0625, "compare": "cross",
    },
    "low_beta": {
        "func": low_beta,
        "data": {"prices": "equity_prices", "equity": "equity_basket"},
        "weight": 0.0625, "compare": "cross",
    },
    "ma_energy": {
        "func": ma_energy,
        "data": {"prices": "equity_prices"},
        "weight": 0.0625, "compare": "cross",
    },
}

# ---- Portfolio construction (port_con.portfolio) ----
# Which method turns the L1 / L2 values into weights:
# "black_litterman" (port_con/black_litterman.py) or "te_budget" (port_con/te_budget.py).
METHOD = "te_budget"

# Shared by both methods.
REBALANCE = "W"  # "W" = last trading day of each week, "M" = of each month
# L1: target vol = baseline vol * (1 + GAMMA * average L1 signal).
GAMMA = 0.2
LEVERAGE_BOUNDS = (0.5, 1.5)
MAX_DEV = 0.10  # max absolute deviation of each sleeve weight from baseline
COV_WINDOW = 756  # trading days of daily returns for the covariance matrix

# TE budget (port_con/te_budget.py). Tracking error vs baseline each layer may use,
# as a share of the whole portfolio. The signals decide direction and size; a layer
# uses its full budget only when its signal is strong. No leverage step.
L1_TE_BUDGET = 0.0075
L1_TE_WEIGHTS = {"saa": 1.0, "taa": 0.0}  # L1 score = sum of layer value x weight; TAA IC ~0 (below)
L2_TE_BUDGET = 0.005
L2_MAX_TILT = 0.05  # max change of one sector's weight, share of the whole portfolio

# Tilt parameters below are calibrated by port_con/calibrate.py from the
# signals' IC on data before CALIBRATION_END (so from then on is out of sample).
CALIBRATION_END = "2023-09-28"
# Default start of the portfolio backtest: the first week every signal has history
# (equity_value starts 2011-09-27), so it shows in sample and out of sample.
BACKTEST_START = "2011-09-30"
# Measured IC (vs next 21 trading days, weekly samples): SAA +0.083,
# TAA -0.009 (-> 0, TAA switched off), L2 +0.025 (recalibrated 2026-09-30
# after the sentiment weight was split over four new L2 signals; was +0.028).

# Black-Litterman.
BL_DELTA = 2.5   # risk aversion: implied returns = BL_DELTA * cov @ baseline weights
BL_TAU = 0.05    # uncertainty of the implied returns (cancels out with the default view confidence)
# View = IC x volatility x score (Grinold & Kahn). IC = how well a score of 1 predicts returns.
# L1: one view, equity minus fixed income, from the SAA and TAA values.
BL_IC_SAA = 0.083
BL_IC_TAA = 0.0
# L2: one view per sector, from its L2 value.
BL_IC_L2 = 0.025
