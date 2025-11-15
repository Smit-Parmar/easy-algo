# backtest/engine_vectorbt.py
import pandas as pd
import vectorbt as vbt
from backtest.base_engine import BaseEngine
from backtest.evaluator import evaluate_backtest

class VectorBTEngine(BaseEngine):
    def __init__(self, data: pd.DataFrame, strategy_cls, config: dict):
        super().__init__(data, strategy_cls, config)

    def run(self, save_html: str | None = None):
        df = self.data.copy()
        # Strategy produces normalized signals
        strategy = self.strategy_cls(df, self.config)
        signals = strategy.generate_signals()  # list of dicts: timestamp,symbol,side,qty

        # Create boolean entry/exit series aligned with df index
        entries = pd.Series(False, index=df.index)
        exits = pd.Series(False, index=df.index)

        for s in signals:
            ts = pd.Timestamp(s["timestamp"])
            if ts not in df.index:
                # skip or find nearest index - here we skip to keep deterministic behavior
                continue
            if s["side"] == "buy":
                entries.at[ts] = True
            else:
                exits.at[ts] = True

        cfg = self.config
        qty = float(cfg.get("qty", 0.01))
        fees = float(cfg.get("commission", 0.0))
        cash = float(cfg.get("cash", 100000.0))

        close = df["close"]

        pf = vbt.Portfolio.from_signals(
            close,
            entries=entries,
            exits=exits,
            init_cash=cash,
            fees=fees,
            size=qty,
            slippage=0.0,
            upon_opposite_entry="reverse",
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
                "pnl": float(row.get("PnL", 0.0))
            })

        meta = {
            "engine": "vectorbt",
            "strategy": self.strategy_cls.__name__,
            "params": self.config
        }

        report = evaluate_backtest(df, trades, save_html=save_html, starting_cash=cash, meta=meta)
        # evaluator expected to return bundle including figure & equity etc.
        return df, trades, report
