import logging
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import List, Tuple

class DataBootstrapValidator:
    """
    Validates that required market data is available.
    Provides clear error messages if data is missing.
    Prevents system from running on fake data.
    """
    def __init__(self, config):
        self.config = config
        self.data_path = Path(config['system_config']['paths']['market_data'])
        self.required_symbols = config['system_config']['data_sources']['follower_assets'] + \
                               [config['system_config']['data_sources']['leader_asset']]
        logging.info(f"DataBootstrapValidator initialized. Required symbols: {self.required_symbols}")

    def validate_symbol_data(self, symbol: str, min_candles: int = 100) -> Tuple[bool, str]:
        """
        Validates that sufficient data exists for a symbol.
        Returns (is_valid, message).
        """
        # Support both 'BTC' and 'BTC/USDT' formats
        if '/' in symbol:
            safe_symbol = symbol.replace('/', '_')
        else:
            safe_symbol = f"{symbol}_USDT"
        
        symbol_path = self.data_path / safe_symbol
        
        if not symbol_path.exists():
            return False, f"No data directory for {symbol}. Expected: {symbol_path}"
        
        parquet_files = list(symbol_path.glob('**/*.parquet'))
        if not parquet_files:
            return False, f"No Parquet files found for {symbol} in {symbol_path}"
        
        try:
            # Try to read a sample to verify integrity
            import pyarrow.parquet as pq
            df = pq.read_table(symbol_path).to_pandas()
            
            if df.empty:
                return False, f"Data for {symbol} is empty"
            
            num_candles = len(df)
            if num_candles < min_candles:
                return False, f"Insufficient candles for {symbol}: {num_candles} < {min_candles}"
            
            # Check required columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return False, f"Missing columns for {symbol}: {missing_cols}"
            
            # Check data quality
            if df['close'].isna().any():
                na_count = df['close'].isna().sum()
                return False, f"Found {na_count} NaN values in close price for {symbol}"
            
            if (df['volume'] == 0).all():
                return False, f"All volumes are zero for {symbol} - data may be corrupted"
            
            return True, f"✓ {symbol}: {num_candles} candles, range {df['timestamp'].min()} to {df['timestamp'].max()}"
        
        except Exception as e:
            return False, f"Error reading {symbol} data: {str(e)}"

    def validate_all_required_symbols(self, min_candles: int = 100) -> Tuple[bool, List[str]]:
        """
        Validates all required symbols.
        Returns (all_valid, list_of_messages).
        """
        messages = []
        all_valid = True
        
        logging.info(f"Validating data for {len(self.required_symbols)} symbols...")
        
        for symbol in self.required_symbols:
            is_valid, msg = self.validate_symbol_data(symbol, min_candles)
            messages.append(msg)
            if not is_valid:
                all_valid = False
                logging.error(f"  ✗ {msg}")
            else:
                logging.info(f"  {msg}")
        
        return all_valid, messages

    def get_bootstrap_instructions(self) -> str:
        """
        Returns human-readable instructions for bootstrapping missing data.
        """
        instructions = "\n" + "="*80 + "\n"
        instructions += "MARKET DATA BOOTSTRAP REQUIRED\n"
        instructions += "="*80 + "\n\n"
        instructions += "Market data directory is empty or insufficient. System cannot operate on fake data.\n\n"
        instructions += "To bootstrap real market data, run:\n\n"
        
        for symbol in self.required_symbols:
            instructions += f"python scripts/load_historical_data.py \\\n"
            instructions += f"  --symbol {symbol} \\\n"
            instructions += f"  --start 2025-06-01T00:00:00Z \\\n"
            instructions += f"  --end 2026-01-31T23:59:59Z \\\n"
            instructions += f"  --timeframe 1h\n\n"
        
        instructions += "Verify data was ingested:\n"
        instructions += f"  ls -la {self.data_path}/\n\n"
        instructions += "="*80 + "\n"
        
        return instructions

    def assert_data_available(self, min_candles: int = 100):
        """
        Asserts that required data is available.
        Raises RuntimeError with bootstrap instructions if not.
        """
        all_valid, messages = self.validate_all_required_symbols(min_candles)
        
        if not all_valid:
            error_msg = "Data validation failed:\n" + "\n".join(messages)
            error_msg += self.get_bootstrap_instructions()
            raise RuntimeError(error_msg)
        
        logging.info("✓ All required market data validated successfully")
