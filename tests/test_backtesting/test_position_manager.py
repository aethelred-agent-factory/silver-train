# tests/test_backtesting/test_position_manager.py
import pytest
from src.backtesting.position_manager import PositionManager


@pytest.fixture
def position_manager(test_config):
    return PositionManager(test_config)


def test_calculate_position_size(position_manager):
    capital = 10000.0
    risk_pct = 1.0
    entry_price = 100.0
    stop_loss_price = 99.0  # 1 unit risk

    size = position_manager.calculate_position_size(
        capital, risk_pct, entry_price, stop_loss_price
    )
    assert size == 100.0  # 10000 * 0.01 / (100-99) = 100

    entry_price = 100.0
    stop_loss_price = 98.0  # 2 unit risk
    size = position_manager.calculate_position_size(
        capital, risk_pct, entry_price, stop_loss_price
    )
    assert size == 50.0  # 10000 * 0.01 / (100-98) = 50


def test_calculate_position_size_invalid_sl(position_manager):
    capital = 10000.0
    risk_pct = 1.0
    entry_price = 100.0
    stop_loss_price = 100.0  # SL at entry

    size = position_manager.calculate_position_size(
        capital, risk_pct, entry_price, stop_loss_price
    )
    assert size == 0.0


def test_place_stop_loss(position_manager):
    entry_price = 100.0
    atr = 2.0
    multiplier = 1.5

    sl = position_manager.place_stop_loss(entry_price, atr, multiplier)
    assert sl == 97.0  # 100 - (2 * 1.5)


def test_place_take_profit(position_manager):
    entry_price = 100.0
    atr = 2.0
    multiplier = 2.0

    tp = position_manager.place_take_profit(entry_price, atr, multiplier)
    assert tp == 104.0  # 100 + (2 * 2.0)
