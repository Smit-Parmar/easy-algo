# backtest/run_backtest.py

import argparse
import importlib
from pathlib import Path

from markets.common.data_factory import get_data_fetcher
from markets.common.data_store import DataStore
from backtest.engine_factory import get_engine


def run_demo_backtest(engine_name="backtestingpy"):
    """
    Runs a demo backtest for any engine (vectorbt / backtestingpy).
    Uses a consistent API so future live-trading integration is seamless.
    """

    # --- Config (kept inline as requested)
    config = {
        "market": "crypto",
        "data_provider": "binance",
        "broker": "paper",
        "strategy": {
            "class": "strategies.vwap_breakout.VWAPBreakout",
            "symbol": "ETHUSDT",
            "timeframe": "5m",

            "session": "W",          # D, W, M
            "mult": 1.0,             # VWAP band multiplier

            "stop_loss": 0.02,        # 2%
            "target_profit": 0.10,    # 10%
            "qty": 1,
            "cash": 6000,
            "commission": 0.0005,
        },
        "start_date": "30-11-2025",
        "end_date": "02-12-2025",
    }

   # --- Load strategy dynamically from config
    strategy_path = config["strategy"]["class"]
    module_name, class_name = strategy_path.rsplit(".", 1)
    StrategyClass = getattr(importlib.import_module(module_name), class_name)

    # --- Prepare data
    store = DataStore(base_path="data/parquet")
    data_fetcher = get_data_fetcher(config["data_provider"], data_store=store)

    print(f"Fetching data for {config['strategy']['symbol']} ...")
    df = data_fetcher.fetch_ohlcv(
        config["strategy"]["symbol"],
        config["strategy"]["timeframe"],
        config.get("start_date"),
        config.get("end_date"),
    )

    # --- Get engine dynamically (via factory)
    EngineClass = get_engine(engine_name)

    # --- Run backtest
    print(f"Running {engine_name.upper()} engine using {StrategyClass.__name__} strategy...")
    engine_runner = EngineClass(df, StrategyClass, config["strategy"])

    #Store inside backtest/reports
    report_dir = Path("backtest/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"backtest_report_{engine_name}.html"
    df, trades, report = engine_runner.run(save_html=str(report_file))

    # --- Print results
    print("\n=== Backtest Stats ===")
    for k, v in report["stats"].items():
        print(f"{k:15s}: {v}")

    print(f"\n✅ Report saved to: {report_file.resolve()}")

    # # Optional: show interactive plots (if in notebook or GUI)
    # try:
    #     report["figure"].show()
    #     report["equity_plot"].show()
    # except Exception:
    #     print("Plotly window skipped (non-GUI environment).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="backtestingpy", help="Choose engine: backtestingpy or vectorbt")
    args = parser.parse_args()
    run_demo_backtest(engine_name=args.engine)
