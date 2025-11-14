# backtest/base_engine.py
from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple, List, Dict, Any

class BaseEngine(ABC):
    def __init__(self, data: pd.DataFrame, strategy_cls, config: dict):
        """
        data: OHLCV dataframe (index = timestamps)
        strategy_cls: class that follows BaseStrategy API (data, config) -> generate_signals()
        config: strategy config dict (params like fast/slow/qty, cash, commission, symbol)
        """
        self.data = data.copy() if data is not None else data
        self.strategy_cls = strategy_cls
        self.config = config or {}

    @abstractmethod
    def run(self, save_html: str | None = None) -> Tuple[pd.DataFrame, List[Dict], Dict[str, Any]]:
        """
        Execute backtest and return (df, trades, report_bundle).
        report_bundle must contain at least: {"stats":..., "equity":..., "figure":..., "meta":...}
        """
        raise NotImplementedError
