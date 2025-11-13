# AlgoTrading Framework (Local, Python)

A modular algo trading platform supporting crypto & Indian markets with backtesting, unified evaluation, visuals, and stats.

---

## ✅ Features up to Phase 6.1

### ✅ Core Architecture
- Modular structure
- StrategyRunner
- Reusable Data + Broker interfaces

### ✅ Market Support
- Binance OHLCV Fetcher
- Parquet caching with DataStore

### ✅ Backtesting Engines
- StrategyRunner (custom)
- BacktestingPyEngine
- VectorBTEngine

### ✅ Unified Evaluation Layer
Works for every engine:
```python
df, trades, report = engine.run()
```

### ✅ Visual + Stats Output
- Plotly candlestick chart
- EMA overlays
- Buy/Sell markers
- Equity curve (Matplotlib)
- Stats:
  - total return
  - sharpe ratio
  - max drawdown
  - win rate
  - trade count

---

## ✅ Usage Example

```python
from backtest.evaluator import evaluate_backtest

report = evaluate_backtest(df, trades, save_html="backtest.html")
print(report["stats"])
report["figure"].show()
report["equity_plot"].show()
```

---

## ✅ Current Folder Structure

```
easy-algo/
├── backtest/
│   ├── engine_backtestingpy.py
│   ├── engine_vectorbt.py
│   ├── evaluator.py
│   ├── run_backtest.py          # CLI entrypoint for quick demo backtests
│   ├── stats_utils.py
│   └── visual_runner.py
├── core/
│   ├── broker_interface.py
│   ├── data_interface.py
│   ├── order_manager.py
│   ├── risk_manager.py
│   └── strategy_runner.py
├── markets/
│   ├── __init__.py
│   ├── common/
│   │   ├── broker_factory.py
│   │   ├── data_factory.py
│   │   ├── data_store.py        # Parquet caching layer
│   │   └── paper_broker.py
│   └── crypto/
│       └── data/
│           ├── binance_data.py  # Binance OHLCV fetcher
│           └── test_binance.py
├── strategies/
│   ├── base_strategy.py
│   ├── ema_crossover.py
│   └── ema_crossover_talib.py
├── utils/
│   └── indicators.py            # EMA helper, etc.
├── visuals/
│   ├── html_report.py
│   ├── mpl_charts.py
│   └── plotly_charts.py
├── data/
│   └── parquet/                 # Cached market data
├── requirements.txt
├── quick_test.py
└── README.md
```

---

## ▶️ Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run a demo backtest (auto-fetches data & caches parquet)
VectorBT engine:
```bash
python -m backtest.run_backtest --engine vectorbt
```

Backtesting.py engine:
```bash
python -m backtest.run_backtest --engine backtestingpy
```

This uses the config embedded in `run_backtest.py`:
```python
config = {
  "market": "crypto",
  "data_provider": "binance",
  "broker": "paper",
  "strategy": {
    "symbol": "ETHUSDT",
    "fast": 9,
    "slow": 21,
    "qty": 1,
    "cash": 10_000_000
  },
  "start_date": "01-11-2024",
  "end_date": "11-11-2025"
}
```

Adjust values (e.g. symbol, dates, EMA periods, qty, cash) directly in the file or refactor to load from a JSON/YAML later.

### 3. Output Artifacts
The run returns a unified tuple:
```python
df, trades, report = engine.run(save_html="backtest_report_vectorbt.html")
```
`report` contains:
- `stats`: dictionary of performance metrics
- `figure`: Plotly candlestick with EMAs & trade markers
- `equity_plot`: Matplotlib equity curve
- Optional saved HTML (`save_html`) combining price + equity views

### 4. Programmatic Usage (without CLI)
```python
from markets.common.data_store import DataStore
from markets.common.data_factory import get_data_fetcher
from backtest.engine_vectorbt import VectorBTEngine
from strategies.ema_crossover_talib import EMACrossoverTALib

config = {"symbol": "BTCUSDT", "fast": 12, "slow": 26, "qty": 0.05, "cash": 50_000}
store = DataStore(base_path="data/parquet")
fetcher = get_data_fetcher("binance", data_store=store)
df = fetcher.fetch_ohlcv(config["symbol"], "5m")

engine = VectorBTEngine(df, EMACrossoverTALib, config)
df, trades, report = engine.run(save_html="btc_backtest.html")
print(report["stats"])  # performance metrics
```

### 5. Evaluator Standalone
If you already have `df` and a trades list in unified format:
```python
from backtest.evaluator import evaluate_backtest
report = evaluate_backtest(df, trades, save_html="custom_report.html")
```

### 6. Unified Trade Format
Each trade dict:
```python
{
  "timestamp": <pd.Timestamp>,
  "symbol": "BTCUSDT",
  "side": "buy" | "sell",
  "qty": 0.01,
  "price": 43210.50,
  # optional: "pnl": float (VectorBT adds this per trade)
}
```

---

## ⚙️ Engines Comparison (Current)
| Engine | Library | Signal Logic | Position Handling | Notes |
| ------ | ------- | ------------ | ----------------- | ----- |
| VectorBTEngine | vectorbt | EMA crossover (fast/slow) | Reverses on opposite signal | Fast & flexible for portfolio extensions |
| BacktestingPyEngine | backtesting.py | EMA crossover (fast/slow) | Closes then flips | Classic strategy backtesting flow |
| StrategyRunner (custom) | pandas | Strategy class `generate_signals()` | Manual fill simulation | Extend for complex multi-leg logic |

---

## 🛠 Custom Strategy (Example)
Implement `generate_signals()` returning a list of dicts:
```python
class MyStrategy(BaseStrategy):
  def generate_signals(self):
    df = self.data
    # ... compute indicators
    return [
      {"timestamp": ts, "symbol": "ETHUSDT", "side": "buy", "qty": 0.1},
      # ...
    ]
```
Plug into any engine expecting `(data, strategy_cls, config)`.

---

## 📈 Roadmap (Next Phases)
Unchanged from earlier, but now foundation expanded with data caching, multiple engines, and unified reporting.

### Phase 7 — Real-time Engine
- Websocket streaming
- Live indicator updates
- Live charting
- Realtime portfolio state

### Phase 8 — Multi-strategy Execution
- One strategy → multiple symbols
- Multiple strategies → one symbol
- Portfolio-level analytics

### Phase 9 — Web Dashboard
- FastAPI backend
- Live plotting
- Position/trade push updates
