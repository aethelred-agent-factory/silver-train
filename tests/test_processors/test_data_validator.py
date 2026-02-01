
from datetime import datetime, timedelta

import pandas as pd
import pytest
from data_bus.market_data_bus import MarketDataBus
from processors.data_validator import DataValidator


@pytest.fixture
def sample_data_with_gaps():
    data = {
        "timestamp": [
            datetime(2023, 1, 1, 0),
            datetime(2023, 1, 1, 1),
            # Missing 2023-01-01, 2
            datetime(2023, 1, 1, 3),
            datetime(2023, 1, 1, 4),
            # Missing 2023-01-01, 5, 6
            datetime(2023, 1, 1, 7),
        ],
        "open": [100, 101, 103, 104, 107],
        "high": [101, 102, 104, 105, 108],
        "low": [99, 100, 102, 103, 106],
        "close": [100, 101, 103, 104, 107],
        "volume": [100, 100, 100, 100, 100],
    }
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@pytest.fixture
def mock_market_data_bus(mocker, sample_data_with_gaps):
    mock = mocker.Mock(spec=MarketDataBus)
    mock.get_candles.return_value = sample_data_with_gaps
    return mock


@pytest.fixture
def data_validator(test_config, mock_market_data_bus):
    return DataValidator(test_config, mock_market_data_bus)


def test_detect_gaps(data_validator, sample_data_with_gaps):
    gaps = data_validator.detect_gaps(sample_data_with_gaps)
    assert not gaps.empty
    assert datetime(2023, 1, 1, 2) in gaps
    assert datetime(2023, 1, 1, 5) in gaps
    assert datetime(2023, 1, 1, 6) in gaps
    assert len(gaps) == 3


def test_impute_missing(data_validator, sample_data_with_gaps):
    imputed_df = data_validator.impute_missing(sample_data_with_gaps)
    assert len(imputed_df) == 8  # Original 5 + 3 missing
    assert (
        imputed_df.loc[
            imputed_df["timestamp"] == datetime(2023, 1, 1, 2), "close"
        ].iloc[0]
        == 101
    )
    assert (
        imputed_df.loc[
            imputed_df["timestamp"] == datetime(2023, 1, 1, 5), "close"
        ].iloc[0]
        == 104
    )
    assert (
        imputed_df.loc[
            imputed_df["timestamp"] == datetime(2023, 1, 1, 5), "volume"
        ].iloc[0]
        == 0
    )


def test_validate_and_impute(data_validator, mock_market_data_bus):
    symbol = "TEST/USDT"
    start = "2023-01-01T00:00:00Z"
    end = "2023-01-01T07:00:00Z"

    imputed_df = data_validator.validate_and_impute(symbol, start, end)
    assert not imputed_df.empty
    mock_market_data_bus.mark_missing.call_count == 3
    assert len(imputed_df) == 8
