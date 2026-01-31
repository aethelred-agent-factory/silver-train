import pandas as pd
import numpy as np
import logging

class RegimeClassifier:
    """
    Classifies the market regime based on indicators and calculates a confidence score.
    """
    def __init__(self, config, indicator_engine):
        self.config = config
        self.indicator_engine = indicator_engine
        self.adx_thresholds = config['regime_config']['adx_thresholds']
        self.atr_percentile_thresholds = config['regime_config']['atr_percentile_thresholds']
        logging.info("Initialized RegimeClassifier.")

    def classify(self, indicators: pd.DataFrame) -> pd.DataFrame:
        """
        Classifies the regime for each timestamp and calculates a confidence score.
        """
        if indicators.empty:
            return pd.DataFrame()

        regime_df = pd.DataFrame(index=indicators.index)
        
        # --- Regime Logic ---
        # Default regime is RANGE
        regime_df['regime'] = 'RANGE'
        # TREND conditions
        is_trending = indicators['adx'] > self.adx_thresholds['trending']
        regime_df.loc[is_trending, 'regime'] = 'TREND'
        # HIGH_VOL conditions (can override trend)
        is_high_vol = indicators['atr_percentile_90'] > self.atr_percentile_thresholds['high_volatility']
        regime_df.loc[is_high_vol, 'regime'] = 'HIGH_VOL'

        # --- Confidence Score Logic ---
        # Confidence is based on how far the ADX is from the thresholds.
        adx = indicators['adx']
        trend_thresh = self.adx_thresholds['trending']
        range_thresh = self.adx_thresholds['ranging']
        
        # Normalize the distance between ranging and trending thresholds
        mid_point = (trend_thresh + range_thresh) / 2
        total_range = trend_thresh - range_thresh
        
        # Calculate confidence based on position within the range
        # Values deep in "ranging" or "trending" zones get higher confidence.
        # Values in the ambiguous middle zone get lower confidence.
        confidence = 1.0 - (np.abs(adx - mid_point) / (total_range / 2)).clip(0, 1)
        confidence = 0.5 + (confidence * 0.5) # Scale to be between 0.5 and 1.0
        
        regime_df['confidence'] = confidence
        
        logging.info("Regime classification complete.")
        return regime_df
        
    def classify_latest(self, symbol: str, start_date: str, end_date: str) -> tuple[str, float]:
        """
        Classifies the latest regime for a given symbol.
        """
        indicators = self.indicator_engine.compute_all(symbol, start_date, end_date)
        if indicators.empty:
            return "UNKNOWN", 0.0
            
        regime_df = self.classify(indicators)
        if regime_df.empty:
            return "UNKNOWN", 0.0
        
        latest_regime = regime_df.iloc[-1]
        return latest_regime['regime'], latest_regime['confidence']