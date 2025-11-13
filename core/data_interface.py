from abc import ABC, abstractmethod
import pandas as pd

class DataInterface(ABC):
    @abstractmethod
    def fetch_ohlcv(self, 
                    symbol: str, 
                    timeframe: str = "1m", 
                    start_date: str | None = None, 
                    end_date: str | None = None,
                    max_cache_age_seconds: int = 3600) -> pd.DataFrame:
        """Fetch OHLCV data for a symbol and timeframe.

        Args:
            symbol: Market symbol (e.g. 'BTCUSDT').
            timeframe: Candle interval (e.g. '1m','5m','1h').
            start_date: Optional start date in dd-mm-YYYY. If None, provider decides.
            end_date: Optional end date in dd-mm-YYYY. If None, up to latest.
            max_cache_age_seconds: Cache freshness threshold when using a data store.
        Returns:
            DataFrame indexed by UTC timestamp with columns open, high, low, close, volume.
        """
        pass

    @abstractmethod
    def subscribe_ticks(self, symbols: list[str], callback):
        pass
