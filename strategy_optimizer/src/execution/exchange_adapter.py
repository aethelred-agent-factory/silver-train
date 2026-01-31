import ccxt
import logging
import time
import os

class ExchangeAdapter:
    """
    CCXT wrapper with rate limiting for interacting with cryptocurrency exchanges.
    """
    def __init__(self, config):
        self.config = config
        self.exchange_name = config['system_config']['data_sources']['default_exchange']
        self.rate_limit = config['system_config']['api']['ccxt']['rate_limit'] / 1000 # seconds
        self.last_request_time = 0

        # Initialize CCXT exchange
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': os.getenv('EXCHANGE_API_KEY'),
            'secret': os.getenv('EXCHANGE_SECRET_KEY'),
            'enableRateLimit': True,
        })
        self.exchange.load_markets()
        logging.info(f"Initialized ExchangeAdapter for {self.exchange_name} with rate limit {self.rate_limit}s.")

    def _rate_limit_pre_check(self):
        """Ensures rate limits are respected before making a request."""
        time_since_last_request = time.time() - self.last_request_time
        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: int = None, limit: int = None):
        """
        Fetches OHLCV data from the exchange.
        """
        self._rate_limit_pre_check()
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        except Exception as e:
            logging.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []

    def create_order(self, symbol: str, type: str, side: str, amount: float, price: float = None):
        """
        Places an order on the exchange.
        """
        self._rate_limit_pre_check()
        try:
            order = self.exchange.create_order(symbol, type, side, amount, price)
            logging.info(f"Created order: {order}")
            return order
        except Exception as e:
            logging.error(f"Error creating order for {symbol}: {e}")
            raise

    def fetch_order_status(self, order_id: str, symbol: str = None):
        """
        Fetches the status of an order.
        """
        self._rate_limit_pre_check()
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logging.error(f"Error fetching order status for {order_id}: {e}")
            raise
