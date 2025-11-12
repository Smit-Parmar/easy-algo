import requests
import pandas as pd
import time

BASE_URL = "https://api.binance.com/api/v3/klines"

class BinanceData:
    def __init__(self):
        self.session = requests.Session()

    def fetch_all_klines(self, symbol, interval, start_time=1502942400000):
        """
        Fetch ALL klines from Binance spot API using proper pagination.
        start_time default = Binance launch (2017).
        """
        print(f"Downloading {symbol} {interval} historical data...")

        limit = 1000
        all_rows = []

        while True:
            print(f"Fetching data starting from {pd.to_datetime(start_time, unit='ms', utc=True)}")
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": start_time
            }

            r = self.session.get(BASE_URL, params=params)
            r.raise_for_status()
            batch = r.json()

            # Stop if no more data
            if not batch:
                break

            for r in batch:
                all_rows.append({
                    "timestamp": pd.to_datetime(r[0], unit="ms", utc=True),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "volume": float(r[5])
                })

            # Pagination: use last OPEN time
            last_open_time = batch[-1][0]

            # Move +1 ms forward
            start_time = last_open_time + 1

            # Avoid hitting rate limit
            time.sleep(0.1)

        df = pd.DataFrame(all_rows).set_index("timestamp")
        print(f"✅ Download complete: {len(df)} rows")

        return df


b = BinanceData()
df = b.fetch_all_klines("BTCUSDT", "15m")
#print df total rown count
print(f"Total rows fetched: {len(df)}")
