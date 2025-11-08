from dataclasses import dataclass
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class Order:
    symbol: str
    qty: float
    side: str
    order_type: str
    price: float | None = None
    order_id: str | None = None
    status: str = "pending"

class OrderManager:
    def __init__(self, broker: Any):
        self.broker = broker
        self.orders: Dict[str, Order] = {}
        self._next_local_id = 1

    def _gen_local_id(self) -> str:
        lid = f"local-{self._next_local_id}"
        self._next_local_id += 1
        return lid

    def create_order(self, symbol: str, qty: float, side: str, order_type: str = "market", price: float | None = None) -> Order:
        local_id = self._gen_local_id()
        order = Order(symbol, qty, side, order_type, price, local_id)
        try:
            resp = self.broker.place_order(symbol, qty, side, order_type, price)
            order.status = resp.get("status", "submitted")
            order.order_id = resp.get("order_id", local_id)
            logger.debug("Order placed: %s", order)
        except Exception as e:
            print("Error placing order:", e)
            order.status = "rejected"
            logger.exception("broker.place_order failed: %s", e)
        self.orders[order.order_id or local_id] = order
        return order

    def cancel_order(self, order_id: str) -> bool:
        if order_id not in self.orders:
            return False
        try:
            ok = self.broker.cancel_order(order_id)
            if ok:
                self.orders[order_id].status = "cancelled"
            return ok
        except Exception:
            logger.exception("failed to cancel order %s", order_id)
            return False

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())
