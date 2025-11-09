# AlgoTrading Platform

This repository contains a modular Python framework for building an **Algo Trading Platform** supporting both Indian and Crypto markets.

## 🚀 Current Phase
**Phase 1** – Core architecture setup with abstract base classes and core order, risk, and strategy orchestration logic.

## 📁 Project Structure
```
AlgoTrading/
├── core/                     # Core abstractions (Phase 1 implemented)
├── markets/                  # Market-specific modules
│   ├── indian/               # Indian brokers & data (Phase 2+)
│   └── crypto/               # Crypto brokers & data (Phase 2+)
├── strategies/               # Strategy definitions
├── backtest/                 # Backtesting engines
├── utils/                    # Common utilities
├── visuals/                  # Charting tools
└── scripts/                  # Demo & test scripts
```

## 🧩 Next Steps
1. Implement `markets/crypto/data/binance_data.py` using Binance API for historical data.
2. Create a paper broker (`markets/common/paper_broker.py`) for simulated orders.
3. Add your first strategy under `strategies/` (e.g., `ema_crossover.py`).
4. Test it using `core/strategy_runner.py` via `scripts/run_backtest_demo.py`.

## ⚙️ Setup Instructions
```bash
# Create virtual env
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Then start building your market adapters and strategies! 🚀
