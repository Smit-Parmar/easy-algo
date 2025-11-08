from __future__ import annotations
import uuid
from typing import Dict, Any, List

class PaperBroker:
    def __init__(self, starting_balances: Dict[str, float] | None = None):
        self.balances = starting_balances or {"USDT": 100000}
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}

    def _gen_id(self) -> str:
        return str(uuid.uuid4())

    def place_order(self, symbol: str, qty: float, side: str, order_type: str, price: float | None = None) -> Dict[str, Any]:
        oid = self._gen_id()
        if order_type == "market":
            fill_price = price if price else 100.0
            self._apply_fill(symbol, qty, side, float(fill_price))
            return {"order_id": oid, "status": "filled", "filled_qty": qty, "avg_price": float(fill_price)}
        else:
            order = {"order_id": oid, "status": "open", "qty": qty, "side": side, "order_type": order_type, "price": price}
            self.orders[oid] = order
            return order

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id]["status"] = "cancelled"
            return True
        return False

    def fetch_open_orders(self) -> List[Dict[str, Any]]:
        return [o for o in self.orders.values() if o.get("status") == "open"]

    def get_positions(self) -> List[Dict[str, Any]]:
        return list(self.positions.values())

    def fetch_account(self) -> Dict[str, Any]:
        return {"balances": self.balances, "positions": self.get_positions()}

    def _apply_fill(self, symbol: str, qty: float, side: str, price: float):
        pos = self.positions.get(symbol, {"symbol": symbol, "qty": 0.0, "avg_price": 0.0})
        if side.lower() == "buy":
            new_qty = pos["qty"] + qty
            if new_qty != 0:
                pos["avg_price"] = (pos["avg_price"] * pos["qty"] + price * qty) / new_qty if pos["qty"] else price
            else:
                pos["avg_price"] = price
            pos["qty"] = new_qty
        else:
            pos["qty"] -= qty
        self.positions[symbol] = pos
