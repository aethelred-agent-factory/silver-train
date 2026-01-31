from typing import Any, Dict, List


class PaperAdapter:
    """
    A paper trading adapter that simulates order execution and portfolio management.
    """

    def __init__(self, initial_balance: float = 100000.0):
        self._balance = initial_balance
        self._positions: Dict[str, float] = {}
        self._orders: List[Dict[str, Any]] = []

    def get_balance(self) -> float:
        return self._balance

    def get_positions(self) -> Dict[str, float]:
        return self._positions

    def create_order(
        self,
        order_id: str,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float = None,
    ) -> Dict[str, Any]:
        if price is None:
            raise ValueError(
                "Paper trading simulation requires a price for all orders."
            )

        if side == "buy":
            if self._balance < amount * price:
                raise ValueError("Insufficient funds to place buy order.")
            self._balance -= amount * price
            self._positions[symbol] = self._positions.get(symbol, 0) + amount
        elif side == "sell":
            if self._positions.get(symbol, 0) < amount:
                raise ValueError("Insufficient position to place sell order.")
            self._balance += amount * price
            self._positions[symbol] -= amount
        else:
            raise ValueError(f"Invalid order side: {side}")

        order = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "status": "closed",
        }
        self._orders.append(order)
        return order
