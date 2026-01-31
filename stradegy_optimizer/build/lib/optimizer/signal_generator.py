import pandas as pd
import logging

class SignalGenerator:
    """
    Scoring system & trade signal generation.
    """
    def __init__(self, config, indicator_engine, regime_classifier):
        self.config = config
        self.indicator_engine = indicator_engine
        self.regime_classifier = regime_classifier
        logging.info("Initialized SignalGenerator.")

    def calculate_signal_score(self, indicators: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Calculates a signal score based on indicators and parameters.
        The scoring system is a simple weighted average of different factors.
        """
        if indicators.empty:
            return pd.DataFrame()

        scores = pd.DataFrame(index=indicators.index)
        
        # RSI-based score
        rsi_score = (100 - indicators['rsi']) / (100 - params.get('rsi_oversold', 30))
        rsi_score = rsi_score.clip(0, 1)

        # Regime-based score
        regime_df = self.regime_classifier.classify(indicators)
        range_score = (regime_df['regime'] == 'RANGE').astype(int)
        trend_score = (regime_df['regime'] == 'TREND').astype(int)
        
        # Weighted score
        w_range = params.get('w_range', 0.33)
        w_rsi = params.get('w_rsi', 0.33)
        w_trend = params.get('w_trend', 0.34)
        
        total_score = (w_range * range_score + w_rsi * rsi_score + w_trend * trend_score) * params.get('base_scale', 3.0)
        
        scores['score'] = total_score
        scores['signal'] = (scores['score'] > params.get('min_score', 2.0)).astype(int)
        
        return scores

    def generate_signals(self, symbol: str, start_date: str, end_date: str, params: dict) -> pd.DataFrame:
        """
        Generates buy/sell signals for a given symbol, date range, and parameter set.
        """
        logging.info(f"Generating signals for {symbol} with params: {params}")
        indicators = self.indicator_engine.compute_all(symbol, start_date, end_date)
        if indicators.empty:
            return pd.DataFrame()
            
        signals = self.calculate_signal_score(indicators, params)
        return pd.concat([indicators, signals], axis=1)