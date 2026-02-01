
from datetime import datetime

import pandas as pd
import pytest
from strategy_optimizer.optimizer.signal_generator import SignalGenerator
from strategy_optimizer.processors.indicator_engine import IndicatorEngine
from strategy_optimizer.processors.regime_classifier import RegimeClassifier


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
def mock_indicator_engine(mocker, sample_ohlcv_data):
    mock = mocker.Mock(spec=IndicatorEngine)
    # Mock compute_all to return a DataFrame with required indicators
    mock_indicators = sample_ohlcv_data.copy()
    mock_indicators["rsi"] = pd.Series([50.0] * len(sample_ohlcv_data))
    mock_indicators["adx"] = pd.Series([20.0] * len(sample_ohlcv_data))
    mock_indicators["atr_percentile_90"] = pd.Series([0.5] * len(sample_ohlcv_data))
    mock.compute_all.return_value = mock_indicators

    # Mock regime_classifier within indicator_engine
    mock_regime_classifier = mocker.Mock(spec=RegimeClassifier)
    mock_regime_df = pd.DataFrame({"regime": ["RANGE"] * len(sample_ohlcv_data)})
    mock_regime_classifier.classify.return_value = mock_regime_df
    mock.regime_classifier = mock_regime_classifier

    return mock


@pytest.fixture
def mock_regime_classifier(mocker):
    mock = mocker.Mock(spec=RegimeClassifier)
    mock_regime_df = pd.DataFrame({"regime": ["RANGE"] * 20})
    mock.classify.return_value = mock_regime_df
    return mock


@pytest.fixture
def signal_generator(test_config, mock_indicator_engine, mock_regime_classifier):
    return SignalGenerator(test_config, mock_indicator_engine, mock_regime_classifier)


def test_calculate_signal_score(signal_generator, mock_indicator_engine):
    # Ensure mock_indicator_engine.compute_all is called first to get indicators
    indicators_df = mock_indicator_engine.compute_all("dummy", "dummy", "dummy")

    params = {
        "min_score": 2.0,
        "rsi_oversold": 30,
        "w_range": 0.5,
        "w_rsi": 0.5,
        "w_trend": 0.0,
        "base_scale": 1.0,
    }
    scores_df = signal_generator.calculate_signal_score(indicators_df, params)

    assert isinstance(scores_df, pd.DataFrame)
    assert "score" in scores_df.columns
    assert "signal" in scores_df.columns
    assert not scores_df.empty


def test_generate_signals(signal_generator):
    symbol = "TEST/USDT"
    start = "2023-01-01T00:00:00Z"
    end = "2023-01-01T19:00:00Z"
    params = {
        "min_score": 2.0,
        "rsi_oversold": 30,
        "w_range": 0.5,
        "w_rsi": 0.5,
        "w_trend": 0.0,
        "base_scale": 1.0,
    }
    signals_df = signal_generator.generate_signals(symbol, start, end, params)

    assert isinstance(signals_df, pd.DataFrame)
    assert "rsi" in signals_df.columns  # From indicators
    assert "score" in signals_df.columns  # From signal generation
    assert "signal" in signals_df.columns
    assert not signals_df.empty
