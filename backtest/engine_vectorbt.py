import vectorbt as vbt
import pandas as pd

class VectorBTEngine:
    def __init__(self, data: pd.DataFrame, strategy_cls, config: dict):
        self.data = data
        self.strategy_cls = strategy_cls
        self.config = config

    def run(self):
        close = self.data['close']
        fast = vbt.MA.run(close, window=self.config.get('fast', 9))
        slow = vbt.MA.run(close, window=self.config.get('slow', 21))
        entries = fast.ma_crossed_above(slow)
        exits = fast.ma_crossed_below(slow)
        pf = vbt.Portfolio.from_signals(
            close,
            entries,
            exits,
            init_cash=self.config.get('cash', 100000),
            fees=self.config.get('commission', 0.001),
            size=self.config.get('qty', 0.01)
        )
        return pf.stats()
