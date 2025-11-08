import pandas as pd
import logging

logger = logging.getLogger(__name__)

class StrategyRunner:
    def __init__(self, data_fetcher, broker, order_manager, strategy_cls, config=None):
        self.data_fetcher = data_fetcher
        self.broker = broker
        self.order_manager = order_manager
        self.strategy_cls = strategy_cls
        self.config = config or {}

    def _prepare_historical(self, symbol: str, timeframe: str, since=None, limit=None):
        df = self.data_fetcher.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df

    def run_backtest(self, symbol: str, timeframe: str, since=None, limit=None):
        df = self._prepare_historical(symbol, timeframe, since, limit)
        strategy = self.strategy_cls(df, self.config.get("strategy", {}))
        signals = strategy.generate_signals()
        trades = []
        for s in signals:
            trade = self.order_manager.create_order(s["symbol"], s["qty"], s["side"], s.get("order_type", "market"), s.get("price"))
            trades.append(trade)
        return trades
