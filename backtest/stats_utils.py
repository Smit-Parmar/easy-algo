# backtest/stats_utils.py

import pandas as pd
import numpy as np

def trades_to_equity_curve(trades, starting_cash=100000.0):
    """Build event-based equity using trade fills at their timestamps (close prices)."""
    if not trades:
        return pd.Series(dtype=float)

    # Sort by time for deterministic equity
    rows = sorted(trades, key=lambda t: pd.Timestamp(t["timestamp"]))

    cash = float(starting_cash)
    pos = {}  # symbol -> qty
    equity_points = []

    for t in rows:
        ts = pd.Timestamp(t["timestamp"])
        price = float(t["price"])
        qty = float(t["qty"])
        side = t["side"]

        if side == "buy":
            cash -= qty * price
            pos[t["symbol"]] = pos.get(t["symbol"], 0.0) + qty
        else:
            cash += qty * price
            pos[t["symbol"]] = pos.get(t["symbol"], 0.0) - qty

        # Mark-to-market using the same fill price for the event moment
        m2m = sum(q * price for q in pos.values())
        equity_points.append((ts, cash + m2m))

    eq = pd.Series([e for _, e in equity_points], index=[ts for ts, _ in equity_points])
    return eq.sort_index()

def compute_sharpe(ret, ann=252):
    if ret.empty:
        return 0.0
    m, s = ret.mean(), ret.std()
    return 0.0 if s == 0 else float((m / s) * (ann ** 0.5))

def max_drawdown(eq: pd.Series):
    if eq.empty:
        return 0.0
    roll_max = eq.cummax()
    drawdown = (eq - roll_max) / roll_max
    return float(drawdown.min())

def compute_stats(trades, equity: pd.Series):
    if equity.empty:
        return {
            "total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0,
            "win_rate": 0.0, "trade_count": 0, "pnl_sum": 0.0
        }
    total = float((equity.iloc[-1] - equity.iloc[0]) / max(1e-9, equity.iloc[0]))
    ret = equity.pct_change().dropna()
    sells = [t for t in trades if t["side"] == "sell"]
    pnl_sum = float(np.nansum([t.get("pnl", 0.0) for t in trades]))
    return {
        "total_return": total,
        "sharpe": compute_sharpe(ret),
        "max_drawdown": max_drawdown(equity),
        "win_rate": (len(sells) / len(trades)) if trades else 0.0,
        "trade_count": len(trades),
        "pnl_sum": pnl_sum,
    }
