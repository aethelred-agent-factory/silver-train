# tests/test_backtesting/test_performance_metrics.py
import pytest
import pandas as pd
import numpy as np
from src.backtesting.performance_metrics import PerformanceMetrics

@pytest.fixture
def sample_equity_curve():
    # A simple equity curve that goes up, then down, then up
    dates = pd.date_range(start='2023-01-01', periods=100)
    equity = pd.Series(np.linspace(1000, 1500, 50).tolist() + np.linspace(1500, 1200, 25).tolist() + np.linspace(1200, 1600, 25).tolist(), index=dates)
    return equity

@pytest.fixture
def performance_metrics(test_config):
    return PerformanceMetrics(test_config)

def test_calculate_sharpe_ratio(performance_metrics, sample_equity_curve):
    sharpe = performance_metrics.calculate_sharpe_ratio(sample_equity_curve)
    assert isinstance(sharpe, float)
    assert sharpe > 0 # Expect positive sharpe for a generally increasing curve

def test_calculate_sortino_ratio(performance_metrics, sample_equity_curve):
    sortino = performance_metrics.calculate_sortino_ratio(sample_equity_curve)
    assert isinstance(sortino, float)
    assert sortino > 0 # Expect positive sortino

def test_calculate_max_drawdown(performance_metrics, sample_equity_curve):
    max_dd = performance_metrics.calculate_max_drawdown(sample_equity_curve)
    assert isinstance(max_dd, float)
    assert max_dd < 0 # Drawdown should be negative or zero
    assert max_dd == pytest.approx(-20.0, abs=0.1) # Approx (1200-1500)/1500 = -0.2 = -20%

def test_calculate_profit_factor(performance_metrics, sample_equity_curve):
    pf = performance_metrics.calculate_profit_factor(sample_equity_curve)
    assert isinstance(pf, float)
    assert pf > 1.0 # Should be > 1 for a profitable strategy

def test_calculate_all_metrics(performance_metrics, sample_equity_curve):
    all_metrics = performance_metrics.calculate_all_metrics(sample_equity_curve, 100, 60)
    assert isinstance(all_metrics, dict)
    assert 'sharpe_ratio' in all_metrics
    assert 'max_drawdown_pct' in all_metrics
    assert 'profit_factor' in all_metrics
    assert 'win_rate' in all_metrics
