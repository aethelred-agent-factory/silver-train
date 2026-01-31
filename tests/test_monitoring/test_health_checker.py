# tests/test_monitoring/test_health_checker.py
import pytest
from src.execution.exchange_adapter import ExchangeAdapter
from src.monitoring.alerting import Alerting
from src.monitoring.health_checker import HealthChecker
from src.storage.state_manager import StateManager


@pytest.fixture
def mock_state_manager(mocker):
    mock = mocker.Mock(spec=StateManager)
    mock.execute_query.return_value = None  # Assume success for query
    return mock


@pytest.fixture
def mock_exchange_adapter(mocker):
    mock = mocker.Mock(spec=ExchangeAdapter)
    mock_exchange = mocker.Mock()
    mock_exchange.fetch_time.return_value = 1234567890  # Simulate successful API call
    mock.exchange = mock_exchange
    return mock


@pytest.fixture
def mock_alerting(mocker):
    mock = mocker.Mock(spec=Alerting)
    mock.send_urgent_alert.return_value = None
    return mock


@pytest.fixture
def health_checker(
    test_config, mock_state_manager, mock_exchange_adapter, mock_alerting
):
    return HealthChecker(
        test_config, mock_state_manager, mock_exchange_adapter, mock_alerting
    )


def test_check_database_connection_success(health_checker, mock_state_manager):
    assert health_checker._check_database_connection() is True
    mock_state_manager.execute_query.assert_called_once_with("SELECT 1;")


def test_check_database_connection_failure(
    health_checker, mock_state_manager, mock_alerting
):
    mock_state_manager.execute_query.side_effect = Exception("DB Error")
    assert health_checker._check_database_connection() is False


def test_check_exchange_api_connection_success(health_checker, mock_exchange_adapter):
    assert health_checker._check_exchange_api_connection() is True
    mock_exchange_adapter.exchange.fetch_time.assert_called_once()


def test_check_exchange_api_connection_failure(health_checker, mock_exchange_adapter):
    mock_exchange_adapter.exchange.fetch_time.side_effect = Exception("API Error")
    assert health_checker._check_exchange_api_connection() is False


def test_run_checks_all_healthy(
    health_checker, mock_state_manager, mock_exchange_adapter, mock_alerting
):
    result = health_checker.run_checks()
    assert result is True
    mock_state_manager.execute_query.assert_called_once()
    mock_exchange_adapter.exchange.fetch_time.assert_called_once()
    mock_alerting.send_urgent_alert.assert_not_called()


def test_run_checks_db_failure(health_checker, mock_state_manager, mock_alerting):
    mock_state_manager.execute_query.side_effect = Exception("DB Error")
    result = health_checker.run_checks()
    assert result is False
    mock_alerting.send_urgent_alert.assert_called_once_with(
        "Database connection failed!"
    )
