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
        More lenient scoring to ensure adequate trade signals.
        """
        if indicators.empty:
            return pd.DataFrame()

        scores = pd.DataFrame(index=indicators.index)
        
        # RSI-based scoring (lower RSI = more oversold = better buy signal)
        rsi_oversold = params.get('rsi_oversold', 30)
        rsi_overbought = params.get('rsi_overbought', 70)
        
        # Score: 1.0 if RSI <= oversold, 0.0 if RSI >= overbought, linear in between
        rsi = indicators['rsi'].fillna(50)  # Neutral middle value if RSI is NaN
        # Clamp RSI to valid range for scoring
        rsi_clamped = rsi.clip(0, 100)
        rsi_score = ((rsi_overbought - rsi_clamped) / (rsi_overbought - rsi_oversold)).clip(0, 1)
        
        # Volume confirmation: prefer higher volume (with fallback for short windows)
        volume_sma = indicators['volume'].rolling(20).mean()
        # If volume_sma is mostly NaN (e.g., in 7-day rapid backtests), use simpler check
        if volume_sma.isna().sum() > len(volume_sma) * 0.5:
            # Use volume > median for short windows, with higher fallback score
            volume_median = indicators['volume'].median()
            volume_score = (indicators['volume'] > volume_median).astype(float).fillna(0.7)  # 0.7 instead of 0.5
        else:
            volume_score = (indicators['volume'] > volume_sma).astype(float).fillna(0.7)
        
        # Combined score: RSI weight 70%, Volume weight 30%
        # This ensures good RSI conditions give ~3.5 score contribution
        total_score = (0.7 * rsi_score + 0.3 * volume_score) * 5.0  # Scale to 0-5
        
        scores['score'] = total_score
        
        # Signal: 1 if score > min_score
        # Lower min_score to ensure we get signals
        min_score = params.get('min_score', 1.5)
        scores['signal'] = 0
        # More lenient: require score > min_score (not >=)
        scores.loc[scores['score'] > min_score, 'signal'] = 1  # Buy signal
        
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