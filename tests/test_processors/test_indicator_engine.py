
from datetime import datetime, timedelta

import pandas as pd
import pytest
from data_bus.market_data_bus import MarketDataBus
from processors.indicator_engine import IndicatorEngine


@pytest.fixture
def sample_ohlcv_data():
    # Create sample OHLCV data for testing
    data = {
        "timestamp": [datetime(2023, 1, 1, h) for h in range(20)],
        "open": [100 + i for i in range(20)],
        "high": [102 + i for i in range(20)],
        "low": [98 + i for i in range(20)],
        "close": [101 + i for i in range(20)],
        "volume": [1000 + i for i in range(20)],
    }
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@pytest.fixture
def mock_market_data_bus(mocker, sample_ohlcv_data):
    mock = mocker.Mock(spec=MarketDataBus)
    mock.get_candles.return_value = sample_ohlcv_data
    return mock


@pytest.fixture
def indicator_engine(test_config, mock_market_data_bus):
    return IndicatorEngine(test_config, mock_market_data_bus)


def test_compute_rsi(indicator_engine, sample_ohlcv_data):
    rsi = indicator_engine.compute_rsi(sample_ohlcv_data)
    assert isinstance(rsi, pd.Series)
    assert not rsi.isnull().all()  # Should have some non-null values


def test_compute_atr(indicator_engine, sample_ohlcv_data):
    atr = indicator_engine.compute_atr(sample_ohlcv_data)
    assert isinstance(atr, pd.Series)
    assert not atr.isnull().all()


def test_compute_adx(indicator_engine, sample_ohlcv_data):
    adx = indicator_engine.compute_adx(sample_ohlcv_data)
    assert isinstance(adx, pd.Series)
    assert not adx.isnull().all()


def test_compute_atr_percentile(indicator_engine, sample_ohlcv_data):
    atr_percentile = indicator_engine.compute_atr_percentile(sample_ohlcv_data)
    assert isinstance(atr_percentile, pd.Series)
    assert not atr_percentile.isnull().all()
    assert all(0 <= p <= 1 for p in atr_percentile.dropna())


def test_compute_all(indicator_engine):
    symbol = "TEST/USDT"
    start = "2023-01-01T00:00:00Z"
    end = "2023-01-01T19:00:00Z"
    all_indicators = indicator_engine.compute_all(symbol, start, end)
    assert isinstance(all_indicators, pd.DataFrame)
    assert not all_indicators.empty
    assert "rsi" in all_indicators.columns
    assert "atr" in all_indicators.columns
    assert "adx" in all_indicators.columns
    assert "atr_percentile_90" in all_indicators.columns
