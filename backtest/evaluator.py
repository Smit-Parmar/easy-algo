# backtest/evaluator.py
from backtest.visual_runner import generate_visuals_and_stats
from visuals.html_report import save_full_html_report

def evaluate_backtest(df, trades, save_html: str | None = None, starting_cash: float = 100000.0, meta: dict | None = None):
    """Compute equity/stats, build figures, and optionally write a single HTML report."""
    bundle = generate_visuals_and_stats(df, trades, starting_cash=starting_cash)
    bundle["meta"] = meta or {}
    bundle["df"] = df
    bundle["trades"] = trades

    if save_html:
        save_full_html_report(
            df=df,
            trades=trades,
            stats=bundle["stats"],
            equity=bundle["equity"],
            outfile=save_html,
            meta=bundle["meta"]
        )
    return bundle
