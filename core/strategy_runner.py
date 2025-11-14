# core/strategy_runner.py
from markets.common.data_factory import get_data_fetcher
from backtest.engine_factory import get_engine
from backtest.evaluator import evaluate_backtest
import logging

logging.basicConfig(level=logging.INFO)

class StrategyRunner:
    def __init__(self, config: dict):
        self.config = config
        self.data_fetcher = get_data_fetcher(config["data_provider"], data_store=None)  # pass store if used

    def run(self, engine_name: str, strategy_cls, symbol: str, timeframe: str, save_html: str | None = None):
        cfg = self.config
        logging.info("Fetching data for %s %s", symbol, timeframe)
        df = self.data_fetcher.fetch_ohlcv(symbol, timeframe, cfg.get("start_date"), cfg.get("end_date"))
        engine_cls = get_engine(engine_name)
        engine_runner = engine_cls(df, strategy_cls, cfg.get("strategy", {}))
        df, trades, report = engine_runner.run(save_html=save_html)
        return df, trades, report
