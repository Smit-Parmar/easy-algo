from abc import ABC, abstractmethod
import pandas as pd

class DataInterface(ABC):
    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, since: str | None = None, limit: int | None = None) -> pd.DataFrame:
        pass

    @abstractmethod
    def subscribe_ticks(self, symbols: list[str], callback):
        pass
