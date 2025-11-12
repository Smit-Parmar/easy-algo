
import pandas as pd
try:
    import talib as ta
except:
    raise ImportError("Install TA-Lib first: pip install TA-Lib")

def ema(series, period):
    values = ta.EMA(series.values.astype(float), timeperiod=period)
    return pd.Series(values, index=series.index, name=f"EMA_{period}")
