# Phase 3: Strategy Integration and Backtesting

## ✅ Implemented
- `strategies/base_strategy.py`: Base class defining the strategy interface.
- `strategies/ema_crossover.py`: Simple EMA crossover strategy.
- `backtest/run_backtest.py`: Demonstrates integration of strategy, data, broker, and order manager.

## ⚙️ How to Run the Demo
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Run the demo backtest:
```bash
python backtest/run_backtest.py
```
3. You should see buy/sell signals executed using Binance data and simulated orders through the PaperBroker.

## 🧠 How It Works
- Data fetched via `BinanceData`
- Strategy generates EMA cross signals
- Orders simulated via `PaperBroker`
- Results printed as executed trade list

## 🚀 Next Steps (Phase 4)
- Add `markets/common/data_store.py` for Parquet caching.
- Introduce detailed stats (PnL, Sharpe ratio, drawdown, etc.).
- Integrate `vectorbt` and `backtesting.py` backtest engines for high performance.
