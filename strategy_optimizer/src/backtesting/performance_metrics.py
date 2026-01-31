import numpy as np
import pandas as pd
import logging

class PerformanceMetrics:
    """
    Calculates various performance metrics from an equity curve.
    """
    def __init__(self, config):
        self.config = config
        self.risk_free_rate = 0.0 # Assuming 0 for simplicity
        logging.info("Initialized PerformanceMetrics.")

    def calculate_sharpe_ratio(self, equity_curve: pd.Series, periods_per_year=252*24) -> float:
        """Calculates the Sharpe ratio."""
        returns = equity_curve.pct_change().dropna()
        if returns.std() == 0:
            return 0
        return (returns.mean() - self.risk_free_rate / periods_per_year) / returns.std() * np.sqrt(periods_per_year)

    def calculate_sortino_ratio(self, equity_curve: pd.Series, periods_per_year=252*24) -> float:
        """Calculates the Sortino ratio."""
        returns = equity_curve.pct_change().dropna()
        downside_returns = returns[returns < 0]
        if downside_returns.std() == 0:
            return 0
        return (returns.mean() - self.risk_free_rate / periods_per_year) / downside_returns.std() * np.sqrt(periods_per_year)

    def calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """Calculates the maximum drawdown."""
        peak = equity_curve.expanding(min_periods=1).max()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min() * 100

    def calculate_profit_factor(self, equity_curve: pd.Series) -> float:
        """Calculates the profit factor."""
        returns = equity_curve.pct_change().dropna()
        gross_profits = returns[returns > 0].sum()
        gross_losses = abs(returns[returns < 0].sum())
        if gross_losses == 0:
            return np.inf
        return gross_profits / gross_losses
        
    def calculate_all_metrics(self, equity_curve: pd.Series, total_trades: int, winning_trades: int) -> dict:
        """Calculates all performance metrics."""
        logging.info("Calculating all performance metrics.")
        
        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0

        metrics = {
            'sharpe_ratio': self.calculate_sharpe_ratio(equity_curve),
            'sortino_ratio': self.calculate_sortino_ratio(equity_curve),
            'max_drawdown_pct': self.calculate_max_drawdown(equity_curve),
            'profit_factor': self.calculate_profit_factor(equity_curve),
            'win_rate': win_rate
        }
        return metrics
