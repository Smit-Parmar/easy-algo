from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BrokerInterface(ABC):
    @abstractmethod
    def place_order(self, symbol: str, qty: float, side: str, order_type: str, price: float | None = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass

    @abstractmethod
    def fetch_open_orders(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def fetch_account(self) -> Dict[str, Any]:
        pass
