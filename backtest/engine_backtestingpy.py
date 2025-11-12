from backtesting import Backtest, Strategy
import pandas as pd
from utils.indicators import ema
from backtest.stats_utils import trades_to_equity_curve, compute_stats
from backtest.evaluator import evaluate_backtest

class BacktestingPyEngine:
    def __init__(self, data: pd.DataFrame, strategy_cls, config: dict):
        self.data = data.copy()
        self.strategy_cls = strategy_cls
        self.config = config

    def run(self,save_html=None):
        cfg = self.config

        # TA-LIB indicators
        df = self.data.copy()
        df["EMA_FAST"] = ema(df["close"], cfg.get("fast", 9))
        df["EMA_SLOW"] = ema(df["close"], cfg.get("slow", 21))

        # Backtesting.py naming rules
        df_bt = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        })

        fast_series = df["EMA_FAST"]
        slow_series = df["EMA_SLOW"]

        class PyStrategy(Strategy):
            def init(self):
                # ✅ Register indicators so Backtesting.py can use them
                self.fast = self.I(lambda: fast_series.values)
                self.slow = self.I(lambda: slow_series.values)

            def next(self):
                f = self.fast[-1]
                s = self.slow[-1]

                if pd.isna(f) or pd.isna(s):
                    return

                if f > s and not self.position:
                    self.buy(size=cfg.get("qty", 0.01))

                elif f < s and self.position:
                    self.sell(size=self.position.size)

        bt = Backtest(
            df_bt,
            PyStrategy,
            cash=cfg.get("cash", 1000000),
            commission=cfg.get("commission", 0.001),
            trade_on_close=True
        )

        stats = bt.run()

        # ✅ Convert BT trades to unified format
        trades = []
        for t in stats._trades.itertuples():
            trades.append({
                "timestamp": t.EntryTime,
                "symbol": cfg["symbol"],
                "side": "buy" if t.Size > 0 else "sell",
                "qty": abs(float(t.Size)),
                "price": float(t.EntryPrice),
            })

        equity = trades_to_equity_curve(trades)
        stats_map = compute_stats(trades, equity)

        report = evaluate_backtest(df, trades, save_html=save_html)

        return df, trades, report
