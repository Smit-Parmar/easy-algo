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

        # ----------------------------------------------------
        # 1. Generate signals from strategy
        # ----------------------------------------------------
        strategy = self.strategy_cls(df, self.config)
        signals = strategy.generate_signals()     # list of signals

        # ----------------------------------------------------
        # 2. Build VectorBT signal arrays
        # ----------------------------------------------------
        long_entries = pd.Series(False, index=df.index)
        long_exits   = pd.Series(False, index=df.index)

        short_entries = pd.Series(False, index=df.index)
        short_exits   = pd.Series(False, index=df.index)

        for s in signals:
            ts = pd.Timestamp(s["timestamp"])
            if ts not in df.index:
                continue

            side = s["side"]

            if side == "buy":
                # Exit short → Enter long
                short_exits.at[ts] = True
                long_entries.at[ts] = True

            elif side == "sell":
                # Exit long → Enter short
                long_exits.at[ts] = True
                short_entries.at[ts] = True
        # ----------------------------------------------------
        # 3. Portfolio execution
        # ----------------------------------------------------
        cfg = self.config
        qty = float(cfg.get("qty", 1))
        fees = float(cfg.get("commission", 0.0))
        cash = float(cfg.get("cash", 100000.0))
        print(f"Starting VectorBT backtest with cash: {cash}, qty: {qty}, fees: {fees}")
        close = df["close"]

        pf = vbt.Portfolio.from_signals(
            close=close,
            entries=long_entries,
            exits=long_exits,
            short_entries=short_entries,
            short_exits=short_exits,
            init_cash=cash,
            fees=fees,
            size=qty,
            slippage=0.0,
            lock_cash=False
        )

        # ----------------------------------------------------
        # 4. Convert VectorBT trades to unified format
        # ----------------------------------------------------
        rec = pf.trades.records_readable
        print("\n===== VectorBT Trades Records =====")
        print(rec)
        trades = []
        for _, row in rec.iterrows():
            timestamp = pd.Timestamp(row["Entry Timestamp"])
            exit_timestamp = pd.Timestamp(row["Exit Timestamp"])
            price = float(row["Avg Entry Price"])
            size = float(row["Size"])
            direction = row["Direction"]
            pnl = float(row["PnL"])

            side = "buy" if direction == "Long" else "sell"

            trades.append({
                "timestamp": timestamp,
                "symbol": cfg.get("symbol", "UNKNOWN"),
                "side": side,
                "qty": abs(size),
                "price": price,
                "exit_timestamp": exit_timestamp,
                "pnl": pnl
            })

        trades = sorted(trades, key=lambda x: x["timestamp"])

        # ----------------------------------------------------
        # 5. Print trades chronologically (optional)
        # ----------------------------------------------------
        print("\n===== Executed Trades (Chronological) =====")
        for t in trades:
            print(
                f"{t['timestamp']} | {t['side'].upper():4} | "
                f"Qty: {t['qty']} | Price: {t['price']} | PnL: {t['pnl']}"
            )
        print("===========================================\n")

        # ----------------------------------------------------
        # 6. Metadata + evaluation
        # ----------------------------------------------------
        meta = {
            "engine": "vectorbt",
            "strategy": self.strategy_cls.__name__,
            "params": self.config
        }

        report = evaluate_backtest(
            df,
            trades,
            save_html=save_html,
            starting_cash=cash,
            meta=meta
        )

        return df, trades, report

