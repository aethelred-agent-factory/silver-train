import logging

import numpy as np
import pandas as pd


class RegimeClassifier:
    """
    Classifies the market regime based on indicators and calculates a confidence score.
    """

    def __init__(self, config, indicator_engine):
        self.config = config
        self.indicator_engine = indicator_engine
        self.adx_thresholds = config["regime_config"]["adx_thresholds"]
        self.atr_percentile_thresholds = config["regime_config"][
            "atr_percentile_thresholds"
        ]
        logging.info("Initialized RegimeClassifier.")

    def classify(self, indicators: pd.DataFrame) -> pd.DataFrame:
        """
        Classifies the regime for each timestamp according to mutually exclusive rules:

        SPEC RULES (3.1.1):
        - TREND: ADX >= 25 AND Volatility <= 70th percentile
        - HIGH_VOL: Volatility >= 70th percentile
        - RANGE: Otherwise

        All trades and performance metrics are tagged with the active regime.
        """
        if indicators.empty:
            return pd.DataFrame()

        regime_df = pd.DataFrame(index=indicators.index)

        # Compute volatility percentile on the entire dataset
        volatility = indicators.get("volatility", pd.Series(0, index=indicators.index))
        vol_percentile = (volatility.rank(pct=True) * 100).fillna(0)

        # Extract ADX values
        adx = indicators.get("adx", pd.Series(0, index=indicators.index)).fillna(0)

        # --- Regime Logic (Mutually Exclusive per spec) ---
        # Start with default: RANGE
        regime_df["regime"] = "RANGE"

        # Rule 1: HIGH_VOL takes precedence (Volatility >= 70th percentile)
        is_high_vol = vol_percentile >= 70
        regime_df.loc[is_high_vol, "regime"] = "HIGH_VOL"

        # Rule 2: TREND (ADX >= 25 AND Volatility < 70th percentile)
        # Only apply TREND where HIGH_VOL is not already set
        trend_threshold = self.adx_thresholds.get("trending", 25)
        is_trend = (adx >= trend_threshold) & ~is_high_vol
        regime_df.loc[is_trend, "regime"] = "TREND"

        # Rule 3: Everything else is RANGE (already default)

        # --- Confidence Score Logic ---
        # Confidence based on distance from threshold midpoint
        trend_thresh = self.adx_thresholds.get("trending", 25)
        range_thresh = self.adx_thresholds.get("ranging", 20)

        # Normalize the distance between ranging and trending thresholds
        mid_point = (trend_thresh + range_thresh) / 2
        total_range = max(1, trend_thresh - range_thresh)  # Avoid division by zero

        # Calculate confidence based on position within the range
        # Values deep in "ranging" or "trending" zones get higher confidence.
        # Values in the ambiguous middle zone get lower confidence.
        confidence = 1.0 - (np.abs(adx - mid_point) / (total_range / 2)).clip(0, 1)
        confidence = 0.5 + (confidence * 0.5)  # Scale to be between 0.5 and 1.0

        regime_df["confidence"] = confidence
        regime_df["volatility_percentile"] = vol_percentile
        regime_df["adx"] = adx

        logging.info(
            f"Regime classification complete. TREND: {(regime_df['regime']=='TREND').sum()}, "
            f"HIGH_VOL: {(regime_df['regime']=='HIGH_VOL').sum()}, "
            f"RANGE: {(regime_df['regime']=='RANGE').sum()}"
        )
        return regime_df

    def classify_latest(
        self, symbol: str, start_date: str, end_date: str
    ) -> tuple[str, float]:
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
        return latest_regime["regime"], latest_regime["confidence"]
