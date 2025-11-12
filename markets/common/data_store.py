import os
import pandas as pd

class DataStore:
    def __init__(self, base_path: str = "data/parquet"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _path(self, symbol: str, timeframe: str, start_date: str = None, end_date: str = None) -> str:
        safe_sym = symbol.replace("/", "_")

        # Default file name if no date range provided
        if start_date is None and end_date is None:
            return os.path.join(self.base_path, f"{safe_sym}_{timeframe}.parquet")

        # File name with date range
        start = start_date.replace("/", "-")
        end = end_date.replace("/", "-") if end_date else "today"

        return os.path.join(self.base_path, f"{safe_sym}_{timeframe}_{start}_{end}.parquet")

    def save(self, df: pd.DataFrame, symbol: str, timeframe: str, start_date: str = None, end_date: str = None) -> str:
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        path = self._path(symbol, timeframe, start_date, end_date)
        df.to_parquet(path)
        return path

    def load(self, symbol: str, timeframe: str, start_date: str = None, end_date: str = None):
        path = self._path(symbol, timeframe, start_date, end_date)
        if not os.path.exists(path):
            return None

        df = pd.read_parquet(path)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        return df

    def append(self, df: pd.DataFrame, symbol: str, timeframe: str,
               start_date: str = None, end_date: str = None) -> str:

        existing = self.load(symbol, timeframe, start_date, end_date)

        if existing is None:
            return self.save(df, symbol, timeframe, start_date, end_date)

        combined = pd.concat([existing, df])
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()

        return self.save(combined, symbol, timeframe, start_date, end_date)

    def last_timestamp(self, symbol: str, timeframe: str,
                       start_date: str = None, end_date: str = None):
        df = self.load(symbol, timeframe, start_date, end_date)
        if df is None or df.empty:
            return None
        return df.index.max()

    def is_stale(self, symbol: str, timeframe: str, max_age_seconds: int,
                 start_date: str = None, end_date: str = None) -> bool:

        ts = self.last_timestamp(symbol, timeframe, start_date, end_date)
        if ts is None:
            return True

        now = pd.Timestamp.utcnow()
        age = (now - ts).total_seconds()

        return age > max_age_seconds
