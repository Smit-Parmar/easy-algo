# Phase 2: Market connectors and Paper Broker

## Implemented
- `markets/crypto/data/binance_data.py`: Binance OHLCV data fetcher
- `markets/common/paper_broker.py`: Simple in-memory simulated broker
- `markets/common/broker_factory.py`: Broker factory
- `markets/common/data_factory.py`: Data fetcher factory

## Quick Test
```python
from markets.common.data_factory import get_data_fetcher
from markets.common.broker_factory import get_broker
from core.order_manager import OrderManager

fetcher = get_data_fetcher('binance')
print(fetcher.fetch_ohlcv('BTCUSDT', '1h'))

broker = get_broker('paper')
om = OrderManager(broker)
ord = om.create_order('BTCUSDT', 0.01, 'buy', 'market', price=100)
print(ord)
```
