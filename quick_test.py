# from markets.common.data_factory import get_data_fetcher
# from markets.common.broker_factory import get_broker
# from core.order_manager import OrderManager

# fetcher = get_data_fetcher('binance')
# print(fetcher.fetch_ohlcv('BTCUSDT', '1h'))  # updated signature (no limit)

# broker = get_broker('paper')
# om = OrderManager(broker)
# order = om.create_order('BTCUSDT', 0.01, 'buy', 'market', price=100)
# print(order)
# print(om.list_orders())




from markets.common.data_store import DataStore
from markets.common.data_factory import get_data_fetcher

store = DataStore(base_path='data/parquet')
fetcher = get_data_fetcher('binance', data_store=store)
df = fetcher.fetch_ohlcv('BTCUSDT', '15m')  # updated signature (no limit)
print(df.tail())