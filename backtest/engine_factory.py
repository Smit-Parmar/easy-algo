# backtest/engine_factory.py
def get_engine(name: str):
    name = (name or "").lower()
    if name == "vectorbt":
        from backtest.engine_vectorbt import VectorBTEngine
        return VectorBTEngine
    elif name == "backtestingpy":
        from backtest.engine_backtestingpy import BacktestingPyEngine
        return BacktestingPyEngine
    elif name == "custom":
        from backtest.engine_custom import CustomEngine
        return CustomEngine
    else:
        raise ValueError(f"Unknown engine: {name}. Supported: vectorbt, backtestingpy, custom")
