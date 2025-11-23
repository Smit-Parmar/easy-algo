# backtest/engine_vectorbt.py
import pandas as pd
import vectorbt as vbt
from backtest.base_engine import BaseEngine


class VectorBTEngine(BaseEngine):
    def __init__(self, data: pd.DataFrame, strategy_cls, config: dict):
        super().__init__(data, strategy_cls, config)

    def run(self, save_html: str | None = None):
        df = self.data.copy()

        # ----------------------------------------------------
        # 1. Generate signals from strategy
        # ----------------------------------------------------
        strategy = self.strategy_cls(df, self.config)
        signals = strategy.generate_signals()     # list of signals (buy/sell)

        # ----------------------------------------------------
        # 2. Build VectorBT-compatible signals (stateful)
        # ----------------------------------------------------
        long_entries = pd.Series(False, index=df.index)
        long_exits   = pd.Series(False, index=df.index)

        short_entries = pd.Series(False, index=df.index)
        short_exits   = pd.Series(False, index=df.index)

        # Sort signals chronologically
        signals_sorted = sorted(signals, key=lambda s: pd.Timestamp(s["timestamp"]))

        # Position state while replaying strategy signals
        pos = 0  # -1 short, 0 flat, +1 long

        for s in signals_sorted:
            ts = pd.Timestamp(s["timestamp"])
            if ts not in df.index:
                continue

            side = s["side"].lower()

            # --------------------------------------------
            # BUY LOGIC
            # --------------------------------------------
            if side == "buy":
                if pos == -1:
                    # EXIT SHORT ONLY
                    short_exits.at[ts] = True
                    pos = 0

                elif pos == 0:
                    # ENTER LONG ONLY
                    long_entries.at[ts] = True
                    pos = 1

                else:
                    # pos == 1: already in long → ignore duplicate buy
                    continue

            # --------------------------------------------
            # SELL LOGIC
            # --------------------------------------------
            elif side == "sell":
                if pos == 1:
                    # EXIT LONG ONLY
                    long_exits.at[ts] = True
                    pos = 0

                elif pos == 0:
                    # ENTER SHORT ONLY
                    short_entries.at[ts] = True
                    pos = -1

                else:
                    # pos == -1: already short → ignore duplicate sell
                    continue

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
        # 6. Metadata + evaluation
        # ----------------------------------------------------
        meta = {
            "engine": "vectorbt",
            "strategy": self.strategy_cls.__name__,
            "params": self.config
        }

        # VectorBT-native stats & equity curve
        equity = pf.value()
        stats = pf.stats()
        report = {
            "equity": equity,
            "stats": stats.to_dict(),
            "meta": meta
        }

        # Save HTML if requested
        if save_html:
            print("Saving VectorBT HTML report to", save_html)
            pf.plot().write_html(save_html)

        return df, trades, report
