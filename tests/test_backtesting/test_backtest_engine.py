# tests/test_backtesting/test_backtest_engine.py
from datetime import datetime, timedelta

import pandas as pd
import pytest
from strategy_optimizer.backtesting.backtest_engine import BacktestEngine
from strategy_optimizer.backtesting.performance_metrics import PerformanceMetrics
from strategy_optimizer.backtesting.position_manager import PositionManager
from strategy_optimizer.data_bus.schemas import BacktestResult
from strategy_optimizer.optimizer.signal_generator import SignalGenerator


@pytest.fixture
def sample_ohlcv_data():
    dates = [datetime(2023, 1, 1, h) for h in range(24)]  # 1 day of hourly data
    data = {
        "timestamp": dates,
        "open": [100 + i for i in range(24)],
        "high": [102 + i for i in range(24)],
        "low": [98 + i for i in range(24)],
        "close": [101 + i for i in range(24)],
        "volume": [1000 + i for i in range(24)],
    }
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@pytest.fixture
def mock_signal_generator(mocker, sample_ohlcv_data):
    mock = mocker.Mock(spec=SignalGenerator)
    # Return a dataframe with an alternating signal for testing
    mock_signals = sample_ohlcv_data.copy()
    mock_signals["signal"] = [
        1 if i % 4 < 2 else 0 for i in range(len(sample_ohlcv_data))
    ]  # Buy for 2 hours, sell for 2 hours
    mock_signals["atr"] = [1.0] * len(sample_ohlcv_data)  # Dummy ATR
    mock.generate_signals.return_value = mock_signals
    return mock


@pytest.fixture
def mock_position_manager(mocker):
    mock = mocker.Mock(spec=PositionManager)
    mock.calculate_position_size.return_value = 1.0  # Always buy 1 unit
    mock.place_stop_loss.return_value = 90.0  # Dummy SL
    return mock


@pytest.fixture
def performance_metrics(test_config):
    return PerformanceMetrics(test_config)


@pytest.fixture
def backtest_engine(
    test_config, mock_signal_generator, mock_position_manager, performance_metrics
):
    return BacktestEngine(
        test_config, mock_signal_generator, mock_position_manager, performance_metrics
    )


def test_run_backtest(backtest_engine):
    symbol = "TEST/USDT"
    start = "2023-01-01T00:00:00Z"
    end = "2023-01-02T23:00:00Z"
    params = {"risk_pct": 1.0, "stop_multiplier": 2.0}

    result = backtest_engine.run_backtest(symbol, start, end, params)

    assert isinstance(result, BacktestResult)
    assert result.total_trades > 0
    assert result.profit_factor > 0  # Should be profitable with increasing prices
    assert len(result.equity_curve) > 0


def test_rapid_backtest(backtest_engine):
    symbol = "TEST/USDT"
    end = "2023-01-02T23:00:00Z"
    params = {"risk_pct": 1.0, "stop_multiplier": 2.0}

    result = backtest_engine.rapid_backtest(symbol, end, params, window_days=1)

    assert isinstance(result, BacktestResult)
    assert result.start_date is not None
    assert result.end_date == pd.to_datetime(end)
    assert len(result.equity_curve) > 0
