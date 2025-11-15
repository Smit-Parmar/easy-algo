# visuals/html_report.py

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path


def save_full_html_report(df, trades, stats, equity, outfile, meta=None):
    """Generate a full HTML backtest report and save it under backtest/reports.

    Parameters
    ----------
    df : pd.DataFrame
        Price/indicator DataFrame (expects open/high/low/close and optional EMA columns).
    trades : list[dict]
        List of trade dictionaries with at least keys: side (buy/sell), timestamp.
    stats : dict
        Mapping of metric name -> value for the stats table.
    equity : pd.Series
        Equity curve indexed by timestamp.
    outfile : str or Path
        Desired output file name or path. If a path with directories is provided, only the
        final file name is used. Automatically appends .html if missing.

    Returns
    -------
    str
        The absolute path to the saved HTML report.
    """
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.65, 0.25, 0.10],
        specs=[[{"type": "xy"}], [{"type": "xy"}], [{"type": "table"}]],
        vertical_spacing=0.03
    )

    # --- Candles
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name="Candles"
    ), row=1, col=1)

    # --- Indicators (fixed colors as requested)
    if "EMA_FAST" in df:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA_FAST"], mode="lines", name="EMA 9",
            line=dict(width=2, color="blue")
        ), row=1, col=1)
    if "EMA_SLOW" in df:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA_SLOW"], mode="lines", name="EMA 21",
            line=dict(width=2, color="red")
        ), row=1, col=1)

    # --- Trades
    buys  = [t for t in trades if t["side"] == "buy"]
    sells = [t for t in trades if t["side"] == "sell"]

    if buys:
        fig.add_trace(go.Scatter(
            x=[pd.Timestamp(t["timestamp"]) for t in buys],
            y=[df.loc[pd.Timestamp(t["timestamp"]), "close"] for t in buys],
            mode="markers",
            marker=dict(size=10, symbol="triangle-up", color="green"),
            name="Buys"
        ), row=1, col=1)

    if sells:
        fig.add_trace(go.Scatter(
            x=[pd.Timestamp(t["timestamp"]) for t in sells],
            y=[df.loc[pd.Timestamp(t["timestamp"]), "close"] for t in sells],
            mode="markers",
            marker=dict(size=10, symbol="triangle-down", color="red"),
            name="Sells"
        ), row=1, col=1)

    # --- Meta info annotation (if provided)
    if meta:
        meta_text = "<br>".join(f"{k}: {v}" for k, v in meta.items() if v is not None)
        fig.add_annotation(
            text=f"<b>Meta:</b><br>{meta_text}",
            xref="paper", yref="paper",
            x=0.01, y=-0.25, showarrow=False,
            align="left", font=dict(size=12, color="gray")
        )
        
    # --- Equity curve
    fig.add_trace(go.Scatter(
        x=equity.index, y=equity.values, mode="lines", name="Equity"
    ), row=2, col=1)

    # --- Stats table
    headers = ["Metric", "Value"]
    rows = [[k, v] for k, v in stats.items()]
    if rows:
        fig.add_trace(go.Table(
            header=dict(values=headers),
            cells=dict(values=list(zip(*rows)))
        ), row=3, col=1)

    fig.update_layout(
        height=900,
        title="Backtest Report",
        xaxis_rangeslider_visible=False,
        showlegend=True
    )
    # --- Determine save location inside backtest/reports
    reports_dir = (Path(__file__).resolve().parent.parent / 'backtest' / 'reports')
    reports_dir.mkdir(parents=True, exist_ok=True)

    out_name = Path(outfile).name  # strip any provided directory structure
    if not out_name.lower().endswith('.html'):
        out_name += '.html'

    final_path = reports_dir / out_name
    fig.write_html(str(final_path), include_plotlyjs="cdn", full_html=True)
    return str(final_path)
