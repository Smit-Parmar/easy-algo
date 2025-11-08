def get_data_fetcher(name: str, **kwargs):
    name = name.lower()
    if name in ("binance", "crypto-binance"):
        from markets.crypto.data.binance_data import BinanceData
        return BinanceData(**kwargs)
    raise ValueError(f"Unknown data fetcher: {name}")
