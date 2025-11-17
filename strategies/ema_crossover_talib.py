
# strategies/ema_crossover_talib.py
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
        position = 0                # +1 long, -1 short, 0 flat
        entry_price = None

        SL = self.config.get("stop_loss", 0.1)        # 10% default
        TP = self.config.get("target_profit", 0.5)    # 50% default

        for ts, row in df.iterrows():
            if pd.isna(row["EMA_FAST"]) or pd.isna(row["EMA_SLOW"]):
                continue

            price = row["close"]
            ema_fast = row["EMA_FAST"]
            ema_slow = row["EMA_SLOW"]

            # ----------------------------------------------------------
            # 1. STOP LOSS / TAKE PROFIT
            # ----------------------------------------------------------
            if position == 1:   # long
                if price <= entry_price * (1 - SL) or price >= entry_price * (1 + TP):
                    # EXIT LONG
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "sell",
                        "qty": self.qty
                    })
                    position = 0
                    entry_price = None
                    continue     # do NOT flip immediately; wait for next EMA signal

            elif position == -1:  # short
                if price >= entry_price * (1 + SL) or price <= entry_price * (1 - TP):
                    # EXIT SHORT
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "buy",
                        "qty": self.qty
                    })
                    position = 0
                    entry_price = None
                    continue

            # ----------------------------------------------------------
            # 2. BUY CONDITION → EMA crossover up
            # ----------------------------------------------------------
            if ema_fast > ema_slow:

                # If already long → do nothing
                if position == 1:
                    continue

                # If short → exit short first
                if position == -1:
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "buy",
                        "qty": self.qty
                    })
                print("Generating BUY signal", ts, price)
                # Enter long
                signals.append({
                    "timestamp": ts,
                    "symbol": self.symbol,
                    "side": "buy",
                    "qty": self.qty
                })
                position = 1
                entry_price = price
                continue

            # ----------------------------------------------------------
            # 3. SELL CONDITION → EMA crossover down
            # ----------------------------------------------------------
            if ema_fast < ema_slow:

                # If already short → do nothing
                if position == -1:
                    continue

                # If long → exit long first
                if position == 1:
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "sell",
                        "qty": self.qty
                    })
                print("Generating SELL signal", ts, price)
                # Enter short
                signals.append({
                    "timestamp": ts,
                    "symbol": self.symbol,
                    "side": "sell",
                    "qty": self.qty
                })
                position = -1
                entry_price = price
                continue

        return signals
