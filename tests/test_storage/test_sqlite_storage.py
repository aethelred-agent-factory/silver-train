import os
import pytest
import json
import pandas as pd
from storage.sqlite_storage import SqliteStorage

@pytest.fixture
def sqlite_storage(tmp_path):
    db_path = str(tmp_path / "test.db")
    artifacts_path = str(tmp_path / "artifacts")
    market_data_path = str(tmp_path / "market")
    storage = SqliteStorage(db_path, artifacts_path, market_data_path)
    return storage

def test_save_load_delete_state(sqlite_storage):
    key = "test_key"
    value = {"a": 1, "b": "hello"}

    # Save
    assert sqlite_storage.save_state(key, value) is True

    # Load
    loaded = sqlite_storage.load_state(key)
    assert loaded == value

    # Delete
    assert sqlite_storage.delete_state(key) is True
    assert sqlite_storage.load_state(key) is None

def test_save_load_artifact(sqlite_storage):
    artifact_id = "test_artifact.json"
    content = {"data": [1, 2, 3]}
    checksum = "abc-123"

    # Save
    assert sqlite_storage.save_artifact(artifact_id, content, checksum) is True

    # Verify file exists
    filepath = os.path.join(sqlite_storage.artifacts_path, artifact_id)
    assert os.path.exists(filepath)
    assert os.path.exists(filepath + ".sha256")

    # Load
    loaded = sqlite_storage.load_artifact(artifact_id)
    assert loaded == content

def test_query_market_data(sqlite_storage, tmp_path):
    # Create a dummy parquet file
    df = pd.DataFrame([
        {"symbol": "BTC/USDT", "timestamp": "2025-01-01 10:00:00", "open": 100, "close": 110},
        {"symbol": "BTC/USDT", "timestamp": "2025-01-01 11:00:00", "open": 110, "close": 120},
        {"symbol": "ETH/USDT", "timestamp": "2025-01-01 10:00:00", "open": 2000, "close": 2100},
    ])
    # SqliteStorage expects safe_symbol file
    safe_symbol = "BTC_USDT"
    df.to_parquet(os.path.join(sqlite_storage.market_data_path, f"{safe_symbol}.parquet"))

    # Query
    results = sqlite_storage.query_market_data("BTC/USDT", "2025-01-01 09:00:00", "2025-01-01 10:30:00")
    assert len(results) == 1
    assert results[0]["symbol"] == "BTC/USDT"
    assert results[0]["open"] == 100
