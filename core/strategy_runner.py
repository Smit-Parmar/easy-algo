
from backtest.evaluator import evaluate_backtest

class StrategyRunner:
    def __init__(self, data_fetcher, broker, order_manager, strategy_cls, config):
        self.data_fetcher = data_fetcher
        self.broker = broker
        self.order_manager = order_manager
        self.strategy_cls = strategy_cls
        self.config = config

    def run_backtest(self, symbol, timeframe, limit=200):
        # Updated fetch_ohlcv signature (limit removed)
        df = self.data_fetcher.fetch_ohlcv(symbol, timeframe)
        strategy = self.strategy_cls(df, self.config["strategy"])
        signals = strategy.generate_signals()

        executed=[]
        for t in signals:
            price=df.loc[t["timestamp"],"close"]
            executed.append({
                "timestamp":t["timestamp"],
                "symbol":t["symbol"],
                "side":t["side"],
                "qty":t["qty"],
                "price":price
            })

        report=evaluate_backtest(df,executed)
        return df,executed,report
