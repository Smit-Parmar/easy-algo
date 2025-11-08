import requests
import pandas as pd

_KLINES_ENDPOINT = "https://api.binance.com/api/v3/klines"
_TF_MAP = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"}

class BinanceData:
    def __init__(self, session=None, data_store=None):
        self.session = session or requests.Session()
        self.data_store = data_store

    def _fetch_from_api(self, symbol, timeframe="1m", since=None, limit=500):
        tf = _TF_MAP.get(timeframe, "1m")
        params = {"symbol": symbol.upper(), "interval": tf, "limit": limit}
        if since is not None:
            params["startTime"] = int(since)
        resp = self.session.get(_KLINES_ENDPOINT, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rows = [{
            "timestamp": pd.to_datetime(r[0], unit="ms", utc=True),
            "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
            "close": float(r[4]), "volume": float(r[5])
        } for r in data]
        return pd.DataFrame(rows).set_index("timestamp")

    def fetch_ohlcv(self, symbol, timeframe="1m", since=None, limit=500, max_cache_age_seconds=3600):
        if self.data_store:
            try:
                #TODO Add the limit in caching logic
                cached = self.data_store.load(symbol, timeframe)
                if cached is not None and not self.data_store.is_stale(symbol, timeframe, max_cache_age_seconds):
                    return cached.tail(limit)
            except Exception:
                pass
        df = self._fetch_from_api(symbol, timeframe, since, limit)
        if self.data_store:
            try:
                self.data_store.append(df, symbol, timeframe)
            except Exception:
                pass
        return df

    def subscribe_ticks(self, symbols, callback):
        raise NotImplementedError("subscribe_ticks not implemented yet.")
