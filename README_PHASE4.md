# Phase 4: Parquet DataStore and Basic Stats

## ✅ Implemented
- `markets/common/data_store.py`: Local parquet caching (save/load/append, staleness check)
- `markets/crypto/data/binance_data.py`: Updated to use DataStore (cache-first behavior)
- `backtest/stats_utils.py`: Equity curve, Sharpe ratio, and max drawdown helpers

## ⚙️ Dependencies
Add these to your `requirements.txt`:
```
pyarrow>=15.0.0
fastparquet>=2024.0.0
```

## 🔁 Cache Flow
1. Data requested via `BinanceData.fetch_ohlcv()`.
2. Checks cache freshness using `DataStore`.
3. Uses cached data if fresh, otherwise fetches from Binance and appends to local parquet.

## 🧪 Example Usage
```python
from markets.common.data_store import DataStore
from markets.common.data_factory import get_data_fetcher

store = DataStore(base_path='data/parquet')
fetcher = get_data_fetcher('binance', data_store=store)
df = fetcher.fetch_ohlcv('BTCUSDT', '1h')
print(df.tail())
```

## 🚀 Next Steps (Phase 5)
- Integrate `backtesting.py` and `vectorbt` under unified backtest engines.
- Add detailed PnL stats, Sharpe/Sortino metrics, and vectorized performance.
- Implement websocket-based live data streaming with incremental caching.
