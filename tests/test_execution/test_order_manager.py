# tests/test_execution/test_order_manager.py
import pytest
from src.execution.exchange_adapter import ExchangeAdapter  # For mocking
from src.execution.order_manager import OrderManager
from src.storage.state_manager import StateManager


@pytest.fixture
def mock_exchange_adapter(mocker):
    mock = mocker.Mock(spec=ExchangeAdapter)
    # Use side_effect to return different order IDs for each call
    call_counter = {"count": 0}

    def create_order_side_effect(*args, **kwargs):
        call_counter["count"] += 1
        return {
            "id": f"mock_order_id_{call_counter['count']}",
            "status": "open",
            "price": 100.0,
        }

    mock.create_order.side_effect = create_order_side_effect
    mock.fetch_order_status.return_value = {
        "id": "mock_order_id_1",
        "status": "closed",
        "filled": 0.01,
        "average": 100.1,
    }
    return mock


@pytest.fixture
def order_manager(test_config, mock_exchange_adapter, in_memory_state_manager):
    return OrderManager(test_config, mock_exchange_adapter, in_memory_state_manager)


@pytest.fixture
def sample_proposal_order():
    return {"proposal_id": "prop_xyz"}


def test_place_order(
    order_manager, mock_exchange_adapter, in_memory_state_manager, sample_proposal_order
):
    symbol = "BTC/USDT"
    side = "buy"
    amount = 0.01
    price = 100.0

    order_id = order_manager.place_order(
        symbol, side, amount, sample_proposal_order, price
    )

    assert order_id == "mock_order_id_1"
    mock_exchange_adapter.create_order.assert_called_once_with(
        symbol, "limit", side, amount, price
    )

    # Verify entry in database
    orders = in_memory_state_manager.execute_query(
        "SELECT * FROM order_log WHERE order_id = ?", ("mock_order_id_1",), fetch="one"
    )
    assert orders is not None
    assert orders[1] == symbol  # symbol
    assert orders[5] == "open"  # status


def test_track_fill(
    order_manager, mock_exchange_adapter, in_memory_state_manager, sample_proposal_order
):
    # First, place an order
    order_id = order_manager.place_order("BTC/USDT", "buy", 0.01, sample_proposal_order)

    # Now, track its fill
    order_manager.track_fill(order_id)

    mock_exchange_adapter.fetch_order_status.assert_called_once_with(order_id, None)

    # Verify update in database
    orders = in_memory_state_manager.execute_query(
        "SELECT * FROM order_log WHERE order_id = ?", (order_id,), fetch="one"
    )
    assert orders[5] == "closed"  # status should be updated
    assert orders[4] == 100.1  # price should be updated (average fill price)


def test_get_order_history(
    order_manager, in_memory_state_manager, sample_proposal_order
):
    order_manager.place_order("ETH/USDT", "sell", 0.1, sample_proposal_order)
    order_manager.place_order("ADA/USDT", "buy", 100, {"proposal_id": "prop_abc"})

    history = order_manager.get_order_history()
    assert len(history) == 2

    filtered_history = order_manager.get_order_history(proposal_id="prop_xyz")
    assert len(filtered_history) == 1
    assert filtered_history[0][1] == "ETH/USDT"
