# tests/test_processors/test_regime_classifier.py
import pytest
import pandas as pd
from datetime import datetime
from src.processors.regime_classifier import RegimeClassifier
from src.processors.indicator_engine import IndicatorEngine # Needs to be mocked

@pytest.fixture
def sample_indicators_data():
    data = {
        'timestamp': [datetime(2023, 1, 1, h) for h in range(10)],
        'adx': [10, 15, 22, 28, 35, 18, 12, 26, 30, 20],
        'atr_percentile_90': [0.1, 0.3, 0.5, 0.8, 0.95, 0.4, 0.2, 0.7, 0.9, 0.6]
    }
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

@pytest.fixture
def mock_indicator_engine(mocker, sample_indicators_data):
    mock = mocker.Mock(spec=IndicatorEngine)
    mock.compute_all.return_value = sample_indicators_data
    return mock

@pytest.fixture
def regime_classifier(test_config, mock_indicator_engine):
    return RegimeClassifier(test_config, mock_indicator_engine)

def test_classify(regime_classifier, sample_indicators_data):
    regimes = regime_classifier.classify(sample_indicators_data)
    assert isinstance(regimes, pd.DataFrame)
    assert 'regime' in regimes.columns
    assert 'confidence' in regimes.columns
    assert len(regimes) == len(sample_indicators_data)

    # Example checks based on sample data and default config
    # Merge the results with the original data to check conditions
    result_df = pd.concat([sample_indicators_data, regimes], axis=1)
    
    # ADX > 25 (trending)
    assert result_df.loc[result_df['adx'] == 28, 'regime'].iloc[0] == 'TREND'
    # HIGH_VOL overrides TREND when ATR_percentile > 0.85
    assert result_df.loc[result_df['atr_percentile_90'] == 0.95, 'regime'].iloc[0] == 'HIGH_VOL'
    # Default is RANGE for low ADX
    assert result_df.loc[result_df['adx'] == 10, 'regime'].iloc[0] == 'RANGE'

def test_classify_latest(regime_classifier):
    symbol = 'TEST/USDT'
    start = '2023-01-01T00:00:00Z'
    end = '2023-01-01T09:00:00Z'
    latest_regime, confidence = regime_classifier.classify_latest(symbol, start, end)
    assert isinstance(latest_regime, str)
    assert isinstance(confidence, float)
    assert latest_regime in ['TREND', 'HIGH_VOL', 'RANGE']
