import pandas as pd
import numpy as np
from strategies.vwap_breakout import VWAPBreakoutTALib

np.random.seed(0)
rows = []
price = 100.0
for i in range(240):  # 10 days of hourly data
    high = price + np.random.rand()*1.5
    low = price - np.random.rand()*1.5
    close = low + (high-low)*np.random.rand()
    volume = np.random.randint(50,150)
    rows.append((high, low, close, volume))
    # induce bigger move every 48 bars (2 days) to simulate breakout potential
    if (i+1) % 48 == 0:
        price += np.random.choice([5,-5])
    else:
        price += np.random.randn()*0.2

idx = pd.date_range('2024-01-01', periods=len(rows), freq='H')
raw_df = pd.DataFrame(rows, columns=['high','low','close','volume'], index=idx)

config = {"session":"D", "mult":2.0, "stop_loss":0.05, "target_profit":0.04, "qty":1, "symbol":"TEST"}
strat = VWAPBreakoutTALib(raw_df, config)
signals = strat.generate_signals()
print("Total signals:", len(signals))
# Basic sanity: no duplicated timestamp entries
from collections import defaultdict
per_ts = defaultdict(list)
for s in signals:
    per_ts[s['timestamp']].append(s['side'])
mult_same = {k:v for k,v in per_ts.items() if len(v)>1}
print("Duplicate timestamp entries:", len(mult_same))
if mult_same:
    print(mult_same)
# Show last few signals
print("Last 5 signals:")
for s in signals[-5:]:
    print(s)
