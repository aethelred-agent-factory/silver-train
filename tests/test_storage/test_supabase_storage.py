import pytest
from unittest.mock import MagicMock, patch
from storage.supabase_storage import SupabaseStorage

@pytest.fixture
def mock_supabase_client():
    with patch("storage.supabase_storage.create_client") as mock_create:
        client = MagicMock()
        mock_create.return_value = client
        yield client

@pytest.fixture
def supabase_storage(mock_supabase_client):
    return SupabaseStorage("https://test.supabase.co", "test-key")

def test_save_state(supabase_storage, mock_supabase_client):
    mock_table = mock_supabase_client.table.return_value

    supabase_storage.save_state("key", {"val": 1})

    mock_supabase_client.table.assert_called_with("optimizer_state")
    mock_table.upsert.assert_called_once_with({"key": "key", "value": {"val": 1}})

def test_load_state(supabase_storage, mock_supabase_client):
    mock_table = mock_supabase_client.table.return_value
    mock_select = mock_table.select.return_value
    mock_eq = mock_select.eq.return_value
    mock_eq.execute.return_value = MagicMock(data=[{"value": {"val": 1}}])

    val = supabase_storage.load_state("key")

    assert val == {"val": 1}
    mock_table.select.assert_called_with("value")
    mock_select.eq.assert_called_with("key", "key")

def test_save_artifact(supabase_storage, mock_supabase_client):
    mock_storage = mock_supabase_client.storage.from_.return_value
    mock_table = mock_supabase_client.table.return_value

    content = {"a": 1}
    supabase_storage.save_artifact("art1", content, "hash1")

    mock_supabase_client.storage.from_.assert_called_with("artifacts")
    # Verify upload called (can't easily verify content_bytes without more complex mock)
    assert mock_storage.upload.called

    # Verify metadata saved
    mock_supabase_client.table.assert_called_with("artifacts")
    mock_table.upsert.assert_called_once_with({
        "id": "art1",
        "checksum": "hash1",
        "uri": "supabase://artifacts/art1"
    })

def test_query_market_data(supabase_storage, mock_supabase_client):
    mock_table = mock_supabase_client.table.return_value
    mock_select = mock_table.select.return_value
    mock_eq = mock_select.eq.return_value
    mock_gte = mock_eq.gte.return_value
    mock_lte = mock_gte.lte.return_value
    mock_lte.execute.return_value = MagicMock(data=[{"symbol": "BTC/USDT", "price": 100}])

    res = supabase_storage.query_market_data("BTC/USDT", "start", "end")

    assert len(res) == 1
    mock_supabase_client.table.assert_called_with("market_data")
    mock_table.select.assert_called_with("*")
    mock_select.eq.assert_called_with("symbol", "BTC/USDT")
    mock_eq.gte.assert_called_with("timestamp", "start")
    mock_gte.lte.assert_called_with("timestamp", "end")
