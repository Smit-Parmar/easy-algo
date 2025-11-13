import argparse
from markets.common.data_factory import get_data_fetcher
from markets.common.broker_factory import get_broker
from markets.common.data_store import DataStore
from core.order_manager import OrderManager
from strategies.ema_crossover import EMACrossover
from strategies.ema_crossover_talib import EMACrossoverTALib

def run_demo_backtest(engine="backtestingpy"):
    config = {
        "market": "crypto",
        "data_provider": "binance",
        "broker": "paper",
        "strategy": {
            "symbol": "ETHUSDT",
            "fast": 9,
            "slow": 21,
            "qty": 1,
            "cash": 10000000
        },
        "start_date": "01-11-2024",
        "end_date": "11-11-2025"
    }

    store = DataStore(base_path='data/parquet')
    data_fetcher = get_data_fetcher(config["data_provider"], data_store=store)
    # Updated signature: removed limit, optional start_date/end_date
    df = data_fetcher.fetch_ohlcv(config['strategy']['symbol'], '5m',config.get("start_date"),config.get("end_date"))

    if engine == "backtestingpy":
        from backtest.engine_backtestingpy import BacktestingPyEngine as Engine
    elif engine == "vectorbt":
        from backtest.engine_vectorbt import VectorBTEngine as Engine

    engine_runner = Engine(df, EMACrossoverTALib, config['strategy'])

    df, trades, report = engine_runner.run(save_html="backtest_report_vectorbt.html")
    # df, trades, report = engine_runner.run(save_html="backtest_report_backtest.html")

    print("\n=== Backtest Stats ===")
    print(report["stats"])

    # ✅ Show visuals
    report["figure"].show()        
    report["equity_plot"].show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="backtestingpy", help="Choose engine: backtestingpy or vectorbt")
    args = parser.parse_args()
    run_demo_backtest(engine=args.engine)
