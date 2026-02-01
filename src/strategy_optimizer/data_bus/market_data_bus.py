import logging
import os
from datetime import datetime
from pathlib import Path

import ccxt
import pandas as pd
from data_bus.schemas import Candle
from storage.interface import StorageInterface


class MarketDataBus:
    """
    Canonical, immutable OHLCV storage.
    """

    def __init__(self, config, storage: StorageInterface):
        self.config = config
        self.storage = storage
        self.exchange_name = config["system_config"]["data_sources"]["default_exchange"]

        # Initialize CCXT exchange
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class(
            {
                "apiKey": os.getenv("EXCHANGE_API_KEY"),
                "secret": os.getenv("EXCHANGE_SECRET_KEY"),
            }
        )
        self.exchange.load_markets()
        logging.info(f"Initialized MarketDataBus with exchange: {self.exchange_name}")

    def ingest_candles(
        self, symbol: str, start_date: str, end_date: str, timeframe="1h"
    ):
        """
        Fetch OHLCV data from the exchange and store it in Parquet format.
        """
        logging.info(f"Ingesting candles for {symbol} from {start_date} to {end_date}")

        since = self.exchange.parse8601(start_date)
        end = self.exchange.parse8601(end_date)

        all_candles = []
        while since < end:
            try:
                candles = self.exchange.fetch_ohlcv(symbol, timeframe, since)
                if not candles:
                    break
                all_candles.extend(candles)
                since = candles[-1][0] + self.exchange.parse_timeframe(timeframe) * 1000
            except Exception as e:
                logging.error(f"Error fetching OHLCV data for {symbol}: {e}")
                break

        if not all_candles:
            logging.warning(f"No candles found for {symbol} in the specified range.")
            return

        df = pd.DataFrame(
            all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df["symbol"] = symbol

        self.storage.save_market_data(symbol, df)
        logging.info(f"Successfully ingested {len(df)} candles for {symbol}")

    def get_candles(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Retrieve candles from storage for a given symbol and date range.
        """
        logging.info(f"Retrieving candles for {symbol} from {start_date} to {end_date}")

        records = self.storage.query_market_data(symbol, start_date, end_date)
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        return df

    def mark_missing(self, symbol: str, timestamp: datetime):
        """
        Track data gaps. (Placeholder for now)
        """
        logging.warning(f"Missing data detected for {symbol} at {timestamp}")
        # In a real implementation, this would write to a log or a database table
        pass
