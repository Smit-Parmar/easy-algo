# Phase 5: Dual Backtest Engines (backtesting.py & vectorbt)

## ✅ Implemented
- `engine_backtestingpy.py`: Backtesting using backtesting.py (traditional trade-by-trade).
- `engine_vectorbt.py`: High-performance vectorized backtesting using vectorbt.
- Updated `run_backtest.py` to support both via CLI flag.

## ⚙️ Usage
```bash
# Run using backtesting.py engine
python -m backtest.run_backtest --engine backtestingpy

# Run using vectorbt engine
python -m backtest.run_backtest --engine vectorbt
```

## 🧠 How It Works
- Both engines share a unified interface (`run()` returning performance stats).
- Easily swap between engines for performance or debugging needs.
- Strategy, broker, and data logic remain the same across both.

## ⚙️ Dependencies
Add to `requirements.txt`:
```
backtesting>=0.3.3
vectorbt>=0.26.1
```

## 🚀 Next Steps (Phase 6)
- Add result visualization and comparison charts.
- Integrate portfolio-level metrics (multi-symbol analysis).
- Develop async event-driven live trading architecture.
