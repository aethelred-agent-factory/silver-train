# tests/test_optimizer/test_fallback_mode.py
import pytest
import random
from src.optimizer.fallback_mode import FallbackMode
from src.backtesting.backtest_engine import BacktestEngine # Needs to be mocked

@pytest.fixture
def mock_backtest_engine(mocker):
    mock = mocker.Mock(spec=BacktestEngine)
    mock.rapid_backtest.return_value.profit_factor = 1.2
    mock.rapid_backtest.return_value.max_drawdown_pct = 10.0
    return mock

@pytest.fixture
def fallback_mode(test_config, mock_backtest_engine):
    # Set a fixed seed for reproducible random choices in tests
    random.seed(42)
    return FallbackMode(test_config, mock_backtest_engine)

def test_perturb_parameters(fallback_mode, mock_backtest_engine, mocker):
    current_params = {
        "min_score": 2.0,
        "rsi_oversold": 30,
        "stop_multiplier": 2.0,
        "risk_pct": 0.5,
        "w_range": 0.33,
        "w_rsi": 0.33,
        "w_trend": 0.34,
        "base_scale": 2.0
    }
    
    # Set up the mock to return progressively better results for each call
    # This ensures that at least one variant will have a better score than baseline
    call_count = {'count': 0}
    def rapid_backtest_side_effect(*args, **kwargs):
        call_count['count'] += 1
        # First call is baseline
        if call_count['count'] == 1:
            return mocker.Mock(profit_factor=1.2, max_drawdown_pct=10.0, total_trades=10)
        # Later calls should have incrementally better profit factor
        else:
            profit_factor = 1.2 + (0.1 * call_count['count'])
            return mocker.Mock(profit_factor=profit_factor, max_drawdown_pct=5.0, total_trades=10)
    
    mock_backtest_engine.rapid_backtest.side_effect = rapid_backtest_side_effect

    perturbed_params = fallback_mode.perturb_parameters(current_params, "BTC/USDT", "2023-01-01T00:00:00Z")
    
    assert isinstance(perturbed_params, dict)
    assert perturbed_params != current_params # Parameters should have changed

def test_revert_to_safe_baseline(fallback_mode):
    safe_params = fallback_mode.revert_to_safe_baseline()
    assert safe_params == fallback_mode.config['safe_baseline']
