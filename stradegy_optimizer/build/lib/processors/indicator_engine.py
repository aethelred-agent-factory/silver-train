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
        
    def compute_atr_percentile(self, data: pd.DataFrame, window: int = 90) -> pd.Series:
        """
        Computes the rolling percentile of ATR.
        """
        atr = self.compute_atr(data)
        atr_percentile = atr.rolling(window=window).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])
        return atr_percentile

    def compute_all(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Computes all indicators for a given symbol and date range.
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
        indicators['atr_percentile_90'] = self.compute_atr_percentile(data)
        
        return pd.concat([data, indicators], axis=1)
