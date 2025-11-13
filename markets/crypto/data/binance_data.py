import requests
import pandas as pd
from datetime import datetime, timedelta

_KLINES_ENDPOINT = "https://api.binance.com/api/v3/klines"
_TF_MAP = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"}

def _to_ms(date_str):
    """Convert dd-mm-yyyy → milliseconds."""
    dt = datetime.strptime(date_str, "%d-%m-%Y")
    return int(dt.timestamp() * 1000)

def _today_ms():
    return int(datetime.utcnow().timestamp() * 1000)


class BinanceData:
    def __init__(self, session=None, data_store=None):
        self.session = session or requests.Session()
        self.data_store = data_store

    def _fetch_from_api(self, symbol, timeframe="1m", start_date=None, end_date=None):
        tf = _TF_MAP.get(timeframe, "1m")

        # Convert dates to ms
        start_ms = _to_ms(start_date) if start_date else 1502942400000   # Binance launch
        end_ms = _to_ms(end_date) if end_date else _today_ms()

        print(f"Fetching {symbol} {tf} from {start_date} to {end_date or 'today'}")

        all_rows = []
        fetch_limit = 1000
        current_start = start_ms

        while True:
            print(f"Fetching data starting from {pd.to_datetime(current_start, unit='ms', utc=True)}")
            params = {
                "symbol": symbol.upper(),
                "interval": tf,
                "limit": fetch_limit,
                "startTime": current_start,
                "endTime": end_ms
            }

            resp = self.session.get(_KLINES_ENDPOINT, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                break

            # Parse candles
            for r in data:
                all_rows.append({
                    "timestamp": pd.to_datetime(r[0], unit="ms", utc=True),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "volume": float(r[5])
                })

            if len(data) < fetch_limit:
                break

            # Pagination using last open time
            last_open_time = data[-1][0]
            current_start = last_open_time + 1  # move forward

        df = pd.DataFrame(all_rows).set_index("timestamp")

        # ✅ Filter final DF inside range
        df = df[(df.index >= pd.to_datetime(start_ms, unit="ms", utc=True)) &
                (df.index <= pd.to_datetime(end_ms, unit="ms", utc=True))]

        print(f"✅ Total rows fetched: {len(df)}")

        return df

    def fetch_ohlcv(self, symbol, timeframe="1m", start_date=None, end_date=None, max_cache_age_seconds=3600):
        if self.data_store:
            try:
                cached = self.data_store.load(symbol, timeframe, start_date, end_date)
                if cached is not None:
                    # Return only within requested date range
                    if start_date:
                        start_ts = _to_ms(start_date)
                        cached = cached[cached.index >= pd.to_datetime(start_ts, unit="ms", utc=True)]
                    if end_date:
                        end_ts = _to_ms(end_date)
                        cached = cached[cached.index <= pd.to_datetime(end_ts, unit="ms", utc=True)]
                    return cached
            except Exception:
                pass

        # Fetch fresh
        df = self._fetch_from_api(symbol, timeframe, start_date, end_date)

        if self.data_store:
            print("Saving fetched data to data store...")
            try:
                self.data_store.append(df, symbol, timeframe,start_date, end_date)
            except Exception:
                pass

        return df

    def subscribe_ticks(self, symbols, callback):
        raise NotImplementedError("subscribe_ticks not implemented yet.")
