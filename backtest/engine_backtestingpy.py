# backtest/engine_backtestingpy.py
from backtesting import Backtest, Strategy
import pandas as pd

class BacktestingPyEngine:
    def __init__(self, data: pd.DataFrame, strategy_cls, config: dict):
        self.data = data
        self.strategy_cls = strategy_cls
        self.config = config

    def run(self):
        # Capture config in closure so inner class can use it
        engine_config = self.config

        class PyStrategy(Strategy):
            def init(self):
                # 'self.data.Close' inside backtesting.py is an _Array-like object.
                # Use self.I with a function that converts the incoming array to pd.Series
                close = self.data.Close
                # fast EMA
                self.ema_fast = self.I(
                    lambda x: pd.Series(x).ewm(span=engine_config.get('fast', 9)).mean().values,
                    close
                )
                # slow EMA
                self.ema_slow = self.I(
                    lambda x: pd.Series(x).ewm(span=engine_config.get('slow', 21)).mean().values,
                    close
                )

            def next(self):
                # Use the most recent values to decide
                if self.ema_fast[-1] > self.ema_slow[-1]:
                    if not self.position:
                        self.buy()
                elif self.ema_fast[-1] < self.ema_slow[-1]:
                    if self.position:
                        self.sell()

        # backtesting.py expects columns Open/High/Low/Close/Volume
        df = self.data.rename(columns={
            "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"
        })
        bt = Backtest(df, PyStrategy,
                      cash=engine_config.get('cash', 100000),
                      commission=engine_config.get('commission', 0.001))
        return bt.run()
