# backtest/stats_utils.py

import pandas as pd
import numpy as np


# -----------------------------
# BASIC METRICS
# -----------------------------
def compute_cagr(eq: pd.Series):
    if eq.empty or len(eq) < 2:
        return 0.0
    start, end = eq.index[0], eq.index[-1]
    years = (end - start).days / 365.25
    if years <= 0:
        return 0.0
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1)


def compute_sharpe(returns, ann_factor=252):
    if returns.empty:
        return 0.0
    mean, std = returns.mean(), returns.std()
    if std == 0:
        return 0.0
    return float((mean / std) * np.sqrt(ann_factor))


def max_drawdown(eq: pd.Series):
    if eq.empty:
        return 0.0
    roll_max = eq.cummax()
    dd = (eq - roll_max) / roll_max
    return float(dd.min())


# -----------------------------
# MASTER STAT FUNCTION
# -----------------------------
def compute_stats(trades, equity: pd.Series):
    """General-purpose stats (platform-neutral)."""

    if equity.empty:
        return {
            "total_return": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "trade_count": len(trades),
            "pnl_sum": 0.0,
            "cagr": 0.0
        }

    returns = equity.pct_change().dropna()

    pnl_list = [t.get("pnl", 0.0) for t in trades]
    pnl_sum = float(np.sum(pnl_list))
    wins = sum(1 for p in pnl_list if p > 0)

    return {
        "total_return": float((equity.iloc[-1] - equity.iloc[0]) / equity.iloc[0]),
        "sharpe": compute_sharpe(returns),
        "max_drawdown": max_drawdown(equity),
        "win_rate": (wins / len(trades)) if trades else 0.0,
        "trade_count": len(trades),
        "pnl_sum": pnl_sum,
        "cagr": compute_cagr(equity),
    }
