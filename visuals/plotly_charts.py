# visuals/plotly_charts.py

import plotly.graph_objects as go

def plot_candles_with_indicators(df, indicators=None, trades=None, title="Backtest Chart"):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Candles"
    ))
    if indicators:
        for name, series in indicators.items():
            line_name = "EMA 9" if "FAST" in name else ("EMA 21" if "SLOW" in name else name)
            fig.add_trace(go.Scatter(x=df.index, y=series, mode='lines', name=line_name))
    if trades:
        buy  = [t for t in trades if t["side"] == "buy"]
        sell = [t for t in trades if t["side"] == "sell"]
        if buy:
            fig.add_trace(go.Scatter(
                x=[t["timestamp"] for t in buy],
                y=[df.loc[t["timestamp"], "close"] for t in buy],
                mode="markers",
                marker=dict(color="green", size=10, symbol="triangle-up"),
                name="Buys"
            ))
        if sell:
            fig.add_trace(go.Scatter(
                x=[t["timestamp"] for t in sell],
                y=[df.loc[t["timestamp"], "close"] for t in sell],
                mode="markers",
                marker=dict(color="red", size=10, symbol="triangle-down"),
                name="Sells"
            ))
    fig.update_layout(height=700, title=title, xaxis_rangeslider_visible=False)
    return fig
