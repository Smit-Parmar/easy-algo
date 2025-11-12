
class BaseStrategy:
    def __init__(self, data, config):
        self.data = data
        self.config = config

    def generate_signals(self):
        raise NotImplementedError
