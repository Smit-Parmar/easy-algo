# backtest/engine_vectorbt.py

import pandas as pd
import vectorbt as vbt
from backtest.evaluator import evaluate_backtest

class VectorBTEngine:
    def __init__(self, data: pd.DataFrame, strategy_cls, config: dict):
        self.data = data.copy()
        self.strategy_cls = strategy_cls  # kept for API symmetry
        self.config = config

    def run(self, save_html: str | None = None):
        df = self.data.copy()
        fast_n = int(self.config.get("fast", 9))
        slow_n = int(self.config.get("slow", 21))

        # Indicators
        df["EMA_FAST"] = df["close"].ewm(span=fast_n, adjust=False).mean()
        df["EMA_SLOW"] = df["close"].ewm(span=slow_n, adjust=False).mean()

        # Unified crossover logic (exactly same as Backtesting.py)
        prev_fast = df["EMA_FAST"].shift(1)
        prev_slow = df["EMA_SLOW"].shift(1)
        entries = (prev_fast <= prev_slow) & (df["EMA_FAST"] > df["EMA_SLOW"])
        exits   = (prev_fast >= prev_slow) & (df["EMA_FAST"] < df["EMA_SLOW"])

        cfg = self.config
        qty = float(cfg.get("qty", 0.01))
        fees = float(cfg.get("commission", 0.001))
        cash = float(cfg.get("cash", 100000))
        print("Initial Cash:", cash,"qty:", qty)
        close = df["close"]

        # Execute on this bar's close (VectorBT does this by default for signals)
        pf = vbt.Portfolio.from_signals(
            close,
            entries=entries,
            exits=exits,
            init_cash=cash,
            fees=fees,
            size=qty,                 # fixed UNITS per trade
            freq=None,                # let vbt infer from index; not needed for stats we compute ourselves
            slippage=0.0,
            upon_opposite_entry="reverse",  # reverse on cross
            lock_cash=False,
        )

        rec = pf.trades.records_readable
        trades = []
        for _, row in rec.iterrows():
            timestamp = row["Entry Timestamp"]
            price = float(row["Avg Entry Price"])
            size = float(row["Size"])
            side = "buy" if size > 0 else "sell"
            trades.append({
                "timestamp": timestamp,
                "symbol": cfg.get("symbol", "UNKNOWN"),
                "side": side,
                "qty": abs(size),
                "price": price,
                "pnl": float(row["PnL"]),
            })

        report = evaluate_backtest(df, trades, save_html=save_html)
        return df, trades, report
