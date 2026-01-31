import logging
import uuid
from datetime import datetime
from typing import Any

class OrderManager:
    """
    Handles order placement and fill tracking.
    """
    def __init__(self, config, exchange_adapter, state_manager):
        self.config = config
        self.exchange_adapter = exchange_adapter
        self.state_manager = state_manager
        self.state_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS order_log (
                order_id TEXT PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                amount REAL,
                price REAL,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                proposal_id TEXT
            );
        """)
        logging.info("Initialized OrderManager.")

    def place_order(self, symbol: str, side: str, amount: float, proposal: Any, price: float = None) -> str:
        """
        Places an order on the exchange and logs it.
        """
        logging.info(f"Placing {side} order for {amount} {symbol} at price {price if price else 'market'}")

        # Generate a unique order ID
        order_id = f"{proposal.proposal_id}-{int(datetime.now().timestamp())}"

        try:
            order_type = 'market' if price is None else 'limit'
            order_info = self.exchange_adapter.create_order(order_id, symbol, order_type, side, amount, price)
            
            status = order_info.get('status', 'open')
            filled_price = order_info.get('price', price)

            self.state_manager.execute_query(
                "INSERT INTO order_log (order_id, symbol, side, amount, price, status, proposal_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_id, symbol, side, amount, filled_price, status, proposal.proposal_id)
            )
            logging.info(f"Order {order_id} placed successfully.")
            return order_id
        except Exception as e:
            logging.error(f"Failed to place order for {symbol}: {e}")
            return None

    def track_fill(self, order_id: str):
        """
        Monitors and updates the status of an order.
        """
        logging.info(f"Tracking fill for order ID: {order_id}")
        
        try:
            order_status = self.exchange_adapter.fetch_order_status(order_id, None)
            status = order_status.get('status')
            filled_amount = order_status.get('filled')
            filled_price = order_status.get('average')

            self.state_manager.execute_query(
                "UPDATE order_log SET status = ?, amount = ?, price = ? WHERE order_id = ?",
                (status, filled_amount, filled_price, order_id)
            )
            logging.info(f"Order {order_id} status updated to {status}. Filled: {filled_amount} @ {filled_price}")
        except Exception as e:
            logging.error(f"Error tracking order {order_id}: {e}")
            
    def get_order_history(self, proposal_id: str = None) -> list:
        """
        Retrieves order history, optionally filtered by proposal ID.
        """
        if proposal_id:
            query = "SELECT * FROM order_log WHERE proposal_id = ?"
            return self.state_manager.execute_query(query, (proposal_id,), fetch='all')
        else:
            query = "SELECT * FROM order_log"
            return self.state_manager.execute_query(query, fetch='all')
