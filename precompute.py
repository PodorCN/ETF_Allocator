import argparse
import shutil
import time

# Runs every slow calculation behind the app once and saves the results to
# cache/results/ (data/results.py), so the pages load them instantly.
# Re-run after new data or code / config changes; old results are replaced.
#
#   python precompute.py                  recompute everything from the cached prices
#   python precompute.py --refresh-data   re-download prices from Yahoo first


def main(refresh_data: bool) -> None:
    from data import results

    if refresh_data:
        from data.universe import get_signal_prices
        print("Downloading prices ...")
        get_signal_prices(force=True)

    shutil.rmtree(results.DIR, ignore_errors=True)

    # Imported after the old results are gone, so every call below computes and saves.
    from attribution.portfolios import PORTFOLIOS
    from pages import brinson, constructor, portfolio_backtest, signal_backtest
    from port_con.config import BACKTEST_START, CALIBRATION_END

    steps = [
        ("ETF Constructor: latest strategy weights", constructor.strategy_weights),
        ("Signal Backtest", signal_backtest.data),
        (f"Portfolio Backtest: performance from {BACKTEST_START}",
         lambda: portfolio_backtest.performance(BACKTEST_START)),
        *[(f"Portfolio Backtest: Brinson, {name}", lambda name=name: brinson.get_attribution(name))
          for name in PORTFOLIOS],
        (f"Portfolio Backtest: signal attribution from {CALIBRATION_END}",
         lambda: portfolio_backtest.attribution(CALIBRATION_END)),
    ]
    total = time.time()
    for label, step in steps:
        t = time.time()
        print(f"{label} ...", end=" ", flush=True)
        step()
        print(f"{time.time() - t:.0f} s")
    print(f"Done in {time.time() - total:.0f} s. Results in {results.DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-data", action="store_true", help="re-download prices from Yahoo first")
    main(parser.parse_args().refresh_data)
