# tests/test_data_bus/test_market_data_bus.py
from datetime import datetime, timedelta

import pandas as pd
import pytest
from src.data_bus.market_data_bus import MarketDataBus


class MockExchange:
    def __init__(self, config=None):
        self.markets = {"BTC/USDT": {"id": "BTCUSDT"}}

    def load_markets(self):
        pass

    def parse8601(self, dt_string):
        return pd.to_datetime(dt_string).timestamp() * 1000

    def parse_timeframe(self, timeframe):
        return 3600  # 1 hour in seconds

    def fetch_ohlcv(self, symbol, timeframe, since):
        # Mock some candle data
        if since >= self.parse8601("2023-01-02T00:00:00Z"):
            return []  # No more data

        start_dt = datetime.fromtimestamp(since / 1000)
        candles = []
        for i in range(10):  # Return 10 candles
            timestamp = (start_dt + timedelta(hours=i)).timestamp() * 1000
            candles.append([timestamp, 100 + i, 105 + i, 95 + i, 102 + i, 1000 + i])
        return candles


@pytest.fixture
def mock_market_data_bus(test_config, temp_data_path, monkeypatch):
    test_config["system_config"]["paths"]["market_data"] = str(temp_data_path)
    monkeypatch.setattr("src.data_bus.market_data_bus.ccxt.binance", MockExchange)
    mdb = MarketDataBus(test_config)
    return mdb


def test_ingest_candles(mock_market_data_bus):
    symbol = "BTC/USDT"
    start = "2023-01-01T00:00:00Z"
    end = "2023-01-01T23:00:00Z"  # Only one batch of 10 candles will be fetched

    mock_market_data_bus.ingest_candles(symbol, start, end)

    df = mock_market_data_bus.get_candles(symbol, start, end)
    assert not df.empty
    assert len(df) > 0
    assert "timestamp" in df.columns
    assert df["timestamp"].iloc[0] == pd.to_datetime("2023-01-01T00:00:00Z")


def test_get_candles(mock_market_data_bus):
    symbol = "BTC/USDT"
    start = "2023-01-01T00:00:00Z"
    end = "2023-01-01T23:00:00Z"
    mock_market_data_bus.ingest_candles(symbol, start, end)

    df = mock_market_data_bus.get_candles(
        symbol, "2023-01-01T05:00:00Z", "2023-01-01T07:00:00Z"
    )
    assert not df.empty
    assert len(df) == 3
    assert df["timestamp"].iloc[0] == pd.to_datetime("2023-01-01T05:00:00Z")
