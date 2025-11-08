import pandas as pd
from strategies.base_strategy import BaseStrategy

class EMACrossover(BaseStrategy):
    def __init__(self, data: pd.DataFrame, config: dict):
        super().__init__(data, config)
        self.fast = config.get("fast_period", 9)
        self.slow = config.get("slow_period", 21)
        self.qty = config.get("qty", 0.01)

    def generate_signals(self):
        df = self.data.copy()
        df["ema_fast"] = df["close"].ewm(span=self.fast, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=self.slow, adjust=False).mean()
        df["signal"] = 0
        df.loc[df["ema_fast"] > df["ema_slow"], "signal"] = 1
        df.loc[df["ema_fast"] < df["ema_slow"], "signal"] = -1

        signals = []
        last_signal = 0
        for ts, row in df.iterrows():
            if row["signal"] != last_signal:
                last_signal = row["signal"]
                if row["signal"] == 1:
                    signals.append({"timestamp": ts, "symbol": self.config.get("symbol", "BTCUSDT"), "side": "buy", "qty": self.qty})
                elif row["signal"] == -1:
                    signals.append({"timestamp": ts, "symbol": self.config.get("symbol", "BTCUSDT"), "side": "sell", "qty": self.qty})
        return signals
