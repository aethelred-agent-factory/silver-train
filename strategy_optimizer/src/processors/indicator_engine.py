import pandas as pd
import numpy as np
import logging

class IndicatorEngine:
    """
    Computes technical indicators like RSI, ATR, ADX from OHLCV data.
    All calculations are causal, using only past data.
    """
    def __init__(self, config, market_data_bus):
        self.config = config
        self.market_data_bus = market_data_bus
        logging.info("Initialized IndicatorEngine.")

    def compute_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Computes the Relative Strength Index (RSI).
        """
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def compute_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Computes the Average True Range (ATR).
        """
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def compute_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Computes the Average Directional Index (ADX).
        """
        plus_dm = data['high'].diff()
        minus_dm = data['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0

        tr1 = pd.DataFrame(data['high'] - data['low'])
        tr2 = pd.DataFrame(abs(data['high'] - data['close'].shift(1)))
        tr3 = pd.DataFrame(abs(data['low'] - data['close'].shift(1)))
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
        atr = tr.rolling(window = period).mean()

        plus_di = 100 * (plus_dm.ewm(alpha = 1/period).mean() / atr)
        minus_di = abs(100 * (minus_dm.ewm(alpha = 1/period).mean() / atr))
        dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
        adx = ((dx.shift(1) * (period - 1)) + dx) / period
        adx_smooth = adx.ewm(alpha = 1/period).mean()
        return adx_smooth
        
    def compute_atr_percentile(self, data: pd.DataFrame, window: int = 14) -> pd.Series:
        """
        Computes the rolling percentile of ATR.
        Uses a smaller effective window to handle small datasets.
        """
        atr = self.compute_atr(data)
        # Use min of window and available non-null values to avoid all-NaN results
        effective_window = max(1, min(window, atr.notna().sum() // 2))
        atr_percentile = atr.rolling(window=effective_window, min_periods=1).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1]
        )
        return atr_percentile

    def compute_volatility(self, data: pd.DataFrame) -> pd.Series:
        """
        Computes volatility as ATR / Close.
        """
        atr = self.compute_atr(data)
        volatility = atr / data['close']
        return volatility

    def compute_range_position(self, data: pd.DataFrame, window: int = 30) -> pd.Series:
        """
        Computes the percentage location of price within the 30-period high/low range.
        Range Position = (Close - Low30) / (High30 - Low30) * 100
        """
        high_30 = data['high'].rolling(window=window, min_periods=1).max()
        low_30 = data['low'].rolling(window=window, min_periods=1).min()
        range_width = high_30 - low_30
        # Avoid division by zero
        range_width = range_width.replace(0, 1)
        range_position = ((data['close'] - low_30) / range_width * 100).clip(0, 100)
        return range_position

    def compute_leader_correlation(self, data: pd.DataFrame, leader_data: pd.DataFrame, window: int = 30) -> pd.Series:
        """
        Computes 30-period rolling correlation versus the Leader (BTC).
        """
        # Ensure data is aligned
        returns = data['close'].pct_change()
        leader_returns = leader_data['close'].pct_change()
        correlation = returns.rolling(window=window, min_periods=1).corr(leader_returns)
        return correlation

    def compute_atr_volatility_percentile(self, data: pd.DataFrame, window: int = 30) -> pd.Series:
        """
        Computes the percentile rank of volatility over a rolling window.
        """
        volatility = self.compute_volatility(data)
        vol_percentile = volatility.rolling(window=window, min_periods=1).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100
        )
        return vol_percentile

    def compute_all(self, symbol: str, start_date: str, end_date: str, leader_symbol: str = None) -> pd.DataFrame:
        """
        Computes all indicators for a given symbol and date range.
        Includes RSI, ATR, ADX, Volatility, Range Position, and Leader Correlation.
        """
        logging.info(f"Computing all indicators for {symbol} from {start_date} to {end_date}")
        data = self.market_data_bus.get_candles(symbol, start_date, end_date)
        if data.empty:
            logging.warning(f"No data found for {symbol}, cannot compute indicators.")
            return pd.DataFrame()
            
        indicators = pd.DataFrame(index=data.index)
        indicators['rsi'] = self.compute_rsi(data)
        indicators['atr'] = self.compute_atr(data)
        indicators['adx'] = self.compute_adx(data)
        indicators['volatility'] = self.compute_volatility(data)
        indicators['atr_percentile_90'] = self.compute_atr_percentile(data)
        indicators['volatility_percentile'] = self.compute_atr_volatility_percentile(data)
        indicators['range_position'] = self.compute_range_position(data)
        
        # Add leader correlation if leader_symbol is provided
        if leader_symbol:
            try:
                leader_data = self.market_data_bus.get_candles(leader_symbol, start_date, end_date)
                if not leader_data.empty:
                    indicators['leader_correlation'] = self.compute_leader_correlation(data, leader_data)
                else:
                    logging.warning(f"No data found for leader {leader_symbol}, skipping correlation.")
                    indicators['leader_correlation'] = 0.0
            except Exception as e:
                logging.warning(f"Failed to compute leader correlation: {e}")
                indicators['leader_correlation'] = 0.0
        
        return pd.concat([data, indicators], axis=1)
