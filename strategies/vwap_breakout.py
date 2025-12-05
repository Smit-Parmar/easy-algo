# strategies/vwap_breakout.py
import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy


class VWAPBreakout(BaseStrategy):
    def __init__(self, data, config):
        super().__init__(data, config)

        self.session = config.get("session", "W")      # D/W/M
        self.mult = float(config.get("mult", 2.0))     # VWAP band multiplier

        self.stop_loss = float(config.get("stop_loss", 0.01))         # 1%
        self.target_profit = float(config.get("target_profit", 0.04)) # 4%

        self.symbol = config.get("symbol", "BTCUSDT")
        self.qty = config.get("qty", 1)

    # -------------------------------------------------------------
    # Helper: detect new session depending on D/W/M
    # -------------------------------------------------------------
    def _is_new_session(self, ts):
        if self.session == "D":
            return ts.date() != self._last_session.date()

        elif self.session == "W":
            return ts.isocalendar().week != self._last_session.isocalendar().week

        elif self.session == "M":
            return (ts.year != self._last_session.year) or (ts.month != self._last_session.month)

        return False

    # -------------------------------------------------------------
    # Core signal generator
    # -------------------------------------------------------------
    def generate_signals(self):
        df = self.data.copy()

        hlc3 = (df["high"] + df["low"] + df["close"]) / 3
        vol = df["volume"]

        # Containers
        vwap = []
        upper = []
        lower = []

        cum_pv = 0.0
        cum_vol = 0.0
        sum_sq = 0.0

        self._last_session = df.index[0]

        # ---------------------------------------------------------
        # 1. Create Anchored VWAP + Bands
        # ---------------------------------------------------------
        for ts, price, vol_i, h3 in zip(df.index, df["close"], vol, hlc3):

            # Session reset
            if self._is_new_session(ts):
                cum_pv = 0.0
                cum_vol = 0.0
                sum_sq = 0.0

            self._last_session = ts

            # VWAP core
            cum_pv += h3 * vol_i
            cum_vol += vol_i
            cur_vwap = cum_pv / cum_vol if cum_vol > 0 else np.nan

            # Std deviation
            sum_sq += (h3 - cur_vwap) ** 2 * vol_i
            var = sum_sq / cum_vol if cum_vol > 0 else 0.0
            stdev = np.sqrt(var)

            vwap.append(cur_vwap)
            upper.append(cur_vwap + self.mult * stdev)
            lower.append(cur_vwap - self.mult * stdev)

        df["VWAP"] = vwap
        df["UPPER"] = upper
        df["LOWER"] = lower

        # ---------------------------------------------------------
        # 2. Generate buy/sell signals (stateful)
        # ---------------------------------------------------------
        signals = []
        position = 0     # +1 long, -1 short, 0 flat
        entry_price = None

        prev_close = None
        prev_upper = None
        prev_lower = None

        for ts, row in df.iterrows():
            close = row["close"]
            up = row["UPPER"]
            lo = row["LOWER"]

            # Need previous values for crossover
            if prev_close is None:
                prev_close = close
                prev_upper = up
                prev_lower = lo
                continue

            # --------------------------
            # STOP LOSS / TAKE PROFIT
            # --------------------------
            if position == 1:  # long
                if close <= entry_price * (1 - self.stop_loss) or close >= entry_price * (1 + self.target_profit):
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "sell",
                        "qty": self.qty
                    })
                    position = 0
                    entry_price = None

            elif position == -1:  # short
                if close >= entry_price * (1 + self.stop_loss) or close <= entry_price * (1 - self.target_profit):
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "buy",
                        "qty": self.qty
                    })
                    position = 0
                    entry_price = None

            # --------------------------
            # BUY — price crosses ABOVE upper band
            # --------------------------
            if prev_close < prev_upper and close > up:
                if position == -1:
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "buy",
                        "qty": self.qty
                    })

                if position <= 0:
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "buy",
                        "qty": self.qty
                    })
                    position = 1
                    entry_price = close

            # --------------------------
            # SELL — price crosses BELOW lower band
            # --------------------------
            if prev_close > prev_lower and close < lo:
                if position == 1:
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "sell",
                        "qty": self.qty
                    })

                if position >= 0:
                    signals.append({
                        "timestamp": ts,
                        "symbol": self.symbol,
                        "side": "sell",
                        "qty": self.qty
                    })
                    position = -1
                    entry_price = close

            prev_close = close
            prev_upper = up
            prev_lower = lo

        return signals
