import argparse
from markets.common.data_factory import get_data_fetcher
from markets.common.broker_factory import get_broker
from markets.common.data_store import DataStore
from core.order_manager import OrderManager
from strategies.ema_crossover import EMACrossover

def run_demo_backtest(engine="backtestingpy"):
    config = {
        "market": "crypto",
        "data_provider": "binance",
        "broker": "paper",
        "strategy": {"symbol": "BTCUSDT", "fast": 9, "slow": 21, "qty": 0.01, "cash": 100000}
    }

    store = DataStore(base_path='data/parquet')
    data_fetcher = get_data_fetcher(config["data_provider"], data_store=store)
    broker = get_broker(config["broker"])
    order_manager = OrderManager(broker)

    df = data_fetcher.fetch_ohlcv(config['strategy']['symbol'], '1h', limit=200)

    if engine == "backtestingpy":
        from backtest.engine_backtestingpy import BacktestingPyEngine as Engine
    elif engine == "vectorbt":
        from backtest.engine_vectorbt import VectorBTEngine as Engine
    else:
        raise ValueError("Unknown engine name")

    print(f"Running {engine} backtest...")
    engine_runner = Engine(df, EMACrossover, config['strategy'])
    result = engine_runner.run()
    print("\n=== Backtest Results ===")
    print(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="backtestingpy", help="Choose engine: backtestingpy or vectorbt")
    args = parser.parse_args()
    run_demo_backtest(engine=args.engine)
