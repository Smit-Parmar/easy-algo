class RiskManager:
    def __init__(self, config: dict):
        self.config = config

    def position_size(self, account_value: float, risk_per_trade: float, stop_distance: float) -> float:
        risk_amount = account_value * risk_per_trade
        if stop_distance <= 0:
            return 0
        return risk_amount / stop_distance

    def check_max_drawdown(self, pnl_history: list[float]) -> bool:
        max_dd = self.config.get("max_drawdown", 0.2)
        if not pnl_history:
            return True
        peak = max(pnl_history)
        trough = min(pnl_history)
        dd = (peak - trough) / (peak if peak else 1)
        return dd <= max_dd
