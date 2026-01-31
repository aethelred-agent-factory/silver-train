import pandas as pd
import logging

class DataValidator:
    """
    Detects missing data and applies imputation.
    """
    def __init__(self, config, market_data_bus):
        self.config = config
        self.market_data_bus = market_data_bus
        logging.info("Initialized DataValidator.")

    def detect_gaps(self, data: pd.DataFrame, expected_freq='h') -> pd.DataFrame:
        """
        Detects gaps in the time series data.
        Returns a DataFrame of missing timestamps.
        """
        if data.empty:
            return pd.DataFrame()
            
        # Ensure timestamp is the index
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.set_index('timestamp')

        # Create the expected date range
        expected_range = pd.date_range(start=data.index.min(), end=data.index.max(), freq=expected_freq)
        
        # Find the missing timestamps
        missing_timestamps = expected_range.difference(data.index)
        
        if len(missing_timestamps) > 0:
            logging.warning(f"Detected {len(missing_timestamps)} missing timestamps.")
            
        return missing_timestamps

    def impute_missing(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Imputes missing data in a reindexed DataFrame.
        """
        if data.empty:
            return pd.DataFrame()

        # Ensure timestamp is the index
        if 'timestamp' in data.columns:
            data = data.set_index('timestamp')
        
        # Create the expected date range and reindex if needed
        expected_range = pd.date_range(start=data.index.min(), end=data.index.max(), freq='h')
        data = data.reindex(expected_range)
        
        # Impute Open/Close with forward-fill
        data['open'] = data['open'].ffill()
        data['close'] = data['close'].ffill()

        # Impute High/Low
        data['high'] = data['high'].fillna(pd.concat([data['open'], data['close']], axis=1).max(axis=1))
        data['low'] = data['low'].fillna(pd.concat([data['open'], data['close']], axis=1).min(axis=1))

        # Impute Volume with 0
        data['volume'] = data['volume'].fillna(0)
        
        logging.info("Missing data imputed.")
        return data.reset_index().rename(columns={'index': 'timestamp'})
        
    def validate_and_impute(self, symbol: str, start_date: str, end_date: str, expected_freq='h') -> pd.DataFrame:
        """
        Fetches data, validates it for missing values, and imputes them.
        """
        data = self.market_data_bus.get_candles(symbol, start_date, end_date)
        if data.empty:
            return pd.DataFrame()
            
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.set_index('timestamp')

        missing_timestamps = self.detect_gaps(data)
        
        if len(missing_timestamps) > 0:
            # Log missing timestamps for audit
            for ts in missing_timestamps:
                self.market_data_bus.mark_missing(symbol, ts)
            
            # Reindex to create gaps, then impute
            expected_range = pd.date_range(start=data.index.min(), end=data.index.max(), freq=expected_freq)
            data = data.reindex(expected_range)
            data = self.impute_missing(data)
            
        return data
