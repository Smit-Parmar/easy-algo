import pandas as pd

class BaseStrategy:
    def __init__(self, data: pd.DataFrame, config: dict):
        self.data = data.copy()
        self.config = config

    def generate_signals(self):
        raise NotImplementedError("Subclasses must implement generate_signals()")
