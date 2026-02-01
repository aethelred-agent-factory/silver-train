# tests/test_backtesting/test_walk_forward.py
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from strategy_optimizer.backtesting.backtest_engine import BacktestEngine
from strategy_optimizer.backtesting.walk_forward import WalkForward
from strategy_optimizer.data_bus.market_data_bus import MarketDataBus
from strategy_optimizer.data_bus.schemas import BacktestResult


@pytest.fixture
def sample_full_data():
    dates = pd.date_range(start="2023-01-01", periods=100, freq="h")
    data = pd.DataFrame(
        {
            "timestamp": dates,
            "open": np.random.rand(100) * 100 + 1000,
            "high": np.random.rand(100) * 100 + 1050,
            "low": np.random.rand(100) * 100 + 950,
            "close": np.random.rand(100) * 100 + 1000,
            "volume": np.random.rand(100) * 1000,
        }
    )
    return data


@pytest.fixture
def mock_market_data_bus(mocker, sample_full_data):
    mock = mocker.Mock(spec=MarketDataBus)
    mock.get_candles.return_value = sample_full_data
    return mock


@pytest.fixture
def mock_backtest_engine(mocker, sample_full_data):
    mock = mocker.Mock(spec=BacktestEngine)
    mock.run_backtest.return_value = BacktestResult(
        start_date=datetime.now(),
        end_date=datetime.now(),
        profit_factor=1.5,
        max_drawdown_pct=5.0,
        total_trades=10,
        win_rate=60.0,
        sharpe_ratio=1.0,
        sortino_ratio=1.5,
        equity_curve=[],
    )
    mock.signal_generator = mocker.Mock()
    mock.signal_generator.indicator_engine = mocker.Mock()
    mock.signal_generator.indicator_engine.market_data_bus = mocker.Mock()
    # Set up the mock to return the sample data
    mock.signal_generator.indicator_engine.market_data_bus.get_candles.return_value = (
        sample_full_data
    )
    return mock


@pytest.fixture
def walk_forward(test_config, mock_backtest_engine):
    return WalkForward(test_config, mock_backtest_engine)


def test_split_datasets(walk_forward, sample_full_data):
    cal, val, test = walk_forward.split_datasets(
        sample_full_data, cal_pct=60, val_pct=20, test_pct=20
    )

    assert len(cal) == 60
    assert len(val) == 20
    assert len(test) == 20

    assert cal.iloc[-1]["timestamp"] < val.iloc[0]["timestamp"]
    assert val.iloc[-1]["timestamp"] < test.iloc[0]["timestamp"]


def test_rolling_walk_forward(walk_forward, mock_backtest_engine):
    symbol = "TEST/USDT"
    start = "2023-01-01T00:00:00Z"
    end = "2023-01-04T00:00:00Z"  # A few days of data
    params = {}
    window_size = 24  # 1 day
    step_size = 12  # 12 hours

    results = walk_forward.rolling_walk_forward(
        symbol, start, end, params, window_size, step_size
    )

    # Based on 100 data points (approx 4 days), with window=24 and step=12
    # Iteration 1: train 0-23, test 24-35
    # Iteration 2: train 12-35, test 36-47
    # ...
    # This will result in a few backtest calls
    assert mock_backtest_engine.run_backtest.call_count > 0
    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(results[0], BacktestResult)
