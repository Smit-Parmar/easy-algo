# backtest/visual_runner.py

from visuals.plotly_charts import plot_candles_with_indicators
from visuals.mpl_charts import plot_equity_curve
from backtest.stats_utils import trades_to_equity_curve, compute_stats

def generate_visuals_and_stats(df, trades, starting_cash=100000.0):
    indicators = {k: df[k] for k in ["EMA_FAST", "EMA_SLOW"] if k in df}

    fig = plot_candles_with_indicators(df, indicators, trades)

    equity = trades_to_equity_curve(trades, starting_cash=starting_cash)
    stats = compute_stats(trades, equity)
    plt = plot_equity_curve(equity)

    return {"figure": fig, "equity_plot": plt, "stats": stats, "equity": equity}
