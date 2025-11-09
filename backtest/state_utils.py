import numpy as np
import pandas as pd

def trades_to_equity_curve(trades, starting_cash=100000.0):
    events = []
    cash = starting_cash
    positions = {}
    for t in trades:
        ts = pd.to_datetime(t.get("timestamp"))
        price = t.get("avg_price") or t.get("price")
        if price is None:
            continue
        side = t.get("side")
        qty = float(t.get("qty", 0))
        if side.lower() == "buy":
            cash -= qty * price
            positions[t["symbol"]] = positions.get(t["symbol"], 0) + qty
        else:
            cash += qty * price
            positions[t["symbol"]] = positions.get(t["symbol"], 0) - qty
        total_equity = cash + sum((positions.get(s, 0) * price) for s in positions)
        events.append((ts, total_equity))
    if not events:
        return pd.Series([], dtype=float)
    events.sort(key=lambda x: x[0])
    idx = pd.DatetimeIndex([e[0] for e in events])
    vals = [e[1] for e in events]
    return pd.Series(vals, index=idx)

def compute_sharpe(returns, annualization=252):
    if returns.empty:
        return 0.0
    mean, std = returns.mean(), returns.std()
    if std == 0:
        return 0.0
    return (mean / std) * (annualization ** 0.5)

def max_drawdown(equity):
    if equity.empty:
        return 0.0
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    return float(drawdown.min())
