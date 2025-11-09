import os
import pandas as pd

class DataStore:
    def __init__(self, base_path: str = "data/parquet"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _path(self, symbol: str, timeframe: str) -> str:
        safe_sym = symbol.replace("/", "_")
        return os.path.join(self.base_path, f"{safe_sym}_{timeframe}.parquet")

    def save(self, df: pd.DataFrame, symbol: str, timeframe: str) -> str:
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        path = self._path(symbol, timeframe)
        df.to_parquet(path)
        return path

    def load(self, symbol: str, timeframe: str):
        path = self._path(symbol, timeframe)
        if not os.path.exists(path):
            return None
        df = pd.read_parquet(path)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df

    def append(self, df: pd.DataFrame, symbol: str, timeframe: str):
        existing = self.load(symbol, timeframe)
        if existing is None:
            return self.save(df, symbol, timeframe)
        combined = pd.concat([existing, df])
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        return self.save(combined, symbol, timeframe)

    def last_timestamp(self, symbol: str, timeframe: str):
        df = self.load(symbol, timeframe)
        if df is None or df.empty:
            return None
        return df.index.max()

    def is_stale(self, symbol: str, timeframe: str, max_age_seconds: int) -> bool:
        ts = self.last_timestamp(symbol, timeframe)
        if ts is None:
            return True
        now = pd.Timestamp.utcnow()
        age = (now - ts).total_seconds()
        return age > max_age_seconds
