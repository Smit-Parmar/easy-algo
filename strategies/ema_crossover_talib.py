
import pandas as pd
from utils.indicators import ema
from strategies.base_strategy import BaseStrategy

class EMACrossoverTALib(BaseStrategy):
    def __init__(self, data, config):
        super().__init__(data, config)
        self.fast = config.get("fast", 9)
        self.slow = config.get("slow", 21)
        self.qty = config.get("qty", 0.01)
        self.symbol = config.get("symbol", "BTCUSDT")

    def generate_signals(self):
        df = self.data.copy()
        df["EMA_FAST"] = ema(df["close"], self.fast)
        df["EMA_SLOW"] = ema(df["close"], self.slow)

        signals = []
        prev = 0
        for ts, row in df.iterrows():
            if pd.isna(row["EMA_FAST"]) or pd.isna(row["EMA_SLOW"]):
                continue
            sig = 1 if row["EMA_FAST"] > row["EMA_SLOW"] else -1
            if sig != prev:
                prev = sig
                if sig == 1:
                    signals.append({"timestamp": ts, "symbol": self.symbol, "side": "buy", "qty": self.qty})
                else:
                    signals.append({"timestamp": ts, "symbol": self.symbol, "side": "sell", "qty": self.qty})
        return signals
