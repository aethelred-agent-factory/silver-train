import os
import ccxt
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime
import logging

from data_bus.schemas import Candle

class MarketDataBus:
    """
    Canonical, immutable OHLCV storage.
    """
    def __init__(self, config):
        self.config = config
        self.data_path = Path(config['system_config']['paths']['market_data'])
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.exchange_name = config['system_config']['data_sources']['default_exchange']
        
        # Initialize CCXT exchange
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': os.getenv('EXCHANGE_API_KEY'),
            'secret': os.getenv('EXCHANGE_SECRET_KEY'),
        })
        self.exchange.load_markets()
        logging.info(f"Initialized MarketDataBus with exchange: {self.exchange_name}")

    def ingest_candles(self, symbol: str, start_date: str, end_date: str, timeframe='1h'):
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

        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['date'] = df['timestamp'].dt.date
        
        # Save to Parquet file, partitioned by date
        table = pa.Table.from_pandas(df)
        safe_symbol = symbol.replace('/', '_')
        pq.write_to_dataset(
            table,
            root_path=self.data_path / safe_symbol,
            partition_cols=['date'],
            basename_template=f"{safe_symbol}-{{i}}.parquet",
            existing_data_behavior='overwrite_or_ignore'
        )
        logging.info(f"Successfully ingested {len(df)} candles for {symbol}")

    def get_candles(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Retrieve candles from storage for a given symbol and date range.
        """
        logging.info(f"Retrieving candles for {symbol} from {start_date} to {end_date}")
        
        safe_symbol = symbol.replace('/', '_')
        dataset_path = self.data_path / safe_symbol
        if not dataset_path.exists():
            logging.warning(f"No data found for symbol: {symbol}")
            return pd.DataFrame()

        filters = []
        if start_date:
            start = pd.to_datetime(start_date, utc=True)
            filters.append(('date', '>=', str(start.date())))
        else:
            start = None

        if end_date:
            end = pd.to_datetime(end_date, utc=True)
            filters.append(('date', '<=', str(end.date())))
        else:
            end = None

        try:
            if filters:
                dataset = pq.ParquetDataset(dataset_path, filters=filters)
            else:
                dataset = pq.ParquetDataset(dataset_path)
        except Exception as e:
            logging.error(f"Error creating ParquetDataset for {symbol} with filters {filters}: {e}")
            # Fallback to reading the whole dataset and filtering in pandas
            dataset = pq.ParquetDataset(dataset_path)

        table = dataset.read(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = table.to_pandas()
        
        # Ensure timestamps are timezone-aware UTC for safe comparisons
        if not pd.api.types.is_datetime64tz_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC')
        
        if start:
            df = df[df['timestamp'] >= start]
        if end:
            df = df[df['timestamp'] <= end]
            
        return df

    def mark_missing(self, symbol: str, timestamp: datetime):
        """
        Track data gaps. (Placeholder for now)
        """
        logging.warning(f"Missing data detected for {symbol} at {timestamp}")
        # In a real implementation, this would write to a log or a database table
        pass
