# tests/test_execution/test_execution_engine.py
import pytest
from src.execution.execution_engine import ExecutionEngine
from src.execution.order_manager import OrderManager # For mocking
from src.data_bus.schemas import OptimizerProposal, AuditVerdict, AuditAction, TieredFinding

@pytest.fixture
def mock_order_manager(mocker):
    mock = mocker.Mock(spec=OrderManager)
    mock.place_order.return_value = "mock_order_id_123"
    return mock

@pytest.fixture
def mock_state_manager(mocker):
    mock = mocker.Mock()
    mock.is_kill_switch_active.return_value = False
    return mock

@pytest.fixture
def mock_portfolio_state(mocker):
    mock = mocker.Mock()
    mock.get_metrics.return_value = {'current_equity': 10000.0}
    mock.max_drawdown_pct = 0.0
    return mock

@pytest.fixture
def execution_engine(test_config, mock_order_manager, mock_state_manager, mock_portfolio_state):
    return ExecutionEngine(test_config, mock_order_manager, mock_state_manager, mock_portfolio_state)

def test_check_governance_approval_block(execution_engine):
    audit_verdict = {"action": {"type": "BLOCK", "reason": "T1_Contradiction"}}
    assert execution_engine._check_governance_approval(audit_verdict) is False

def test_check_governance_approval_allow_with_restriction(execution_engine):
    audit_verdict = {"action": {"type": "ALLOW_WITH_RESTRICTION", "restrictions": {"max_order_size_pct": 0.5}}}
    assert execution_engine._check_governance_approval(audit_verdict) is True

def test_check_governance_approval_allow(execution_engine):
    audit_verdict = {"action": {"type": "ALLOW"}}
    assert execution_engine._check_governance_approval(audit_verdict) is True

def test_execute_trade_blocked_by_kill_switch(execution_engine, mock_state_manager, mock_order_manager):
    mock_state_manager.is_kill_switch_active.return_value = True
    signal = {"symbol": "BTC/USDT", "signal": 1}
    proposal = {"proposal_id": "prop1"}
    audit_verdict = {"action": {"type": "ALLOW"}}

    result = execution_engine.execute_trade(signal, proposal, audit_verdict)
    assert result is False
    mock_order_manager.place_order.assert_not_called()

def test_execute_trade_blocked_by_audit(execution_engine, mock_order_manager):
    signal = {"symbol": "BTC/USDT", "signal": 1}
    proposal = {"proposal_id": "prop1"}
    audit_verdict = {"action": {"type": "BLOCK", "reason": "T1_Contradiction"}}
    
    result = execution_engine.execute_trade(signal, proposal, audit_verdict)
    assert result is False
    mock_order_manager.place_order.assert_not_called()

def test_execute_trade_allowed(execution_engine, mock_order_manager):
    signal = {"symbol": "BTC/USDT", "signal": 1, "amount": 0.01}
    proposal = {"proposal_id": "prop1"}
    audit_verdict = {"action": {"type": "ALLOW"}}
    
    result = execution_engine.execute_trade(signal, proposal, audit_verdict)
    assert result is True
    mock_order_manager.place_order.assert_called_once()

def test_execute_trade_allowed_with_restriction(execution_engine, mock_order_manager):
    signal = {"symbol": "BTC/USDT", "signal": 1, "amount": 0.01}
    proposal = {"proposal_id": "prop1"}
    audit_verdict = {"action": {"type": "ALLOW_WITH_RESTRICTION", "restrictions": {"max_order_size_pct": 0.5}}}
    
    result = execution_engine.execute_trade(signal, proposal, audit_verdict)
    assert result is True
    # Verify that the amount passed to place_order was restricted
    mock_order_manager.place_order.assert_called_once_with(
        "BTC/USDT", "buy", 0.01 * 0.5, proposal
    )
