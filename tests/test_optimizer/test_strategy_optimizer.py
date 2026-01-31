# tests/test_optimizer/test_strategy_optimizer.py
from datetime import datetime

import pytest
from src.data_bus.event_bus import EventBus
from src.data_bus.schemas import OptimizerProposal
from src.optimizer.strategy_optimizer import StrategyOptimizer
from src.processors.regime_classifier import RegimeClassifier


@pytest.fixture
def mock_regime_classifier(mocker):
    mock = mocker.Mock(spec=RegimeClassifier)
    mock.classify_latest.return_value = ("TREND", 0.9)
    return mock


@pytest.fixture
def mock_llm_interface(mocker):
    mock = mocker.Mock()
    mock.query_llm.return_value = {"min_score": 2.5, "rsi_oversold": 32}
    return mock


@pytest.fixture
def mock_fallback_mode(mocker):
    mock = mocker.Mock()
    mock.perturb_parameters.return_value = {"min_score": 2.2, "rsi_oversold": 33}
    return mock


@pytest.fixture
def mock_parameter_memory(mocker):
    mock = mocker.Mock()
    mock.has_been_tested.return_value = False
    mock.log_tested.return_value = None
    return mock


@pytest.fixture
def event_bus_optimizer(in_memory_state_manager):
    return EventBus(in_memory_state_manager)


@pytest.fixture
def strategy_optimizer(
    test_config,
    mock_regime_classifier,
    mock_llm_interface,
    mock_fallback_mode,
    mock_parameter_memory,
    event_bus_optimizer,
):
    return StrategyOptimizer(
        test_config,
        mock_regime_classifier,
        mock_llm_interface,
        mock_fallback_mode,
        mock_parameter_memory,
        event_bus_optimizer,
    )


def test_propose_parameters(strategy_optimizer, event_bus_optimizer):
    current_metrics = {"max_drawdown_pct": 10.0, "profit_factor": 1.5, "profit": 5.0}
    regime = "TREND"
    history = {}  # Placeholder

    # propose_parameters returns a tuple in v2
    params, action, reasoning = strategy_optimizer.propose_parameters(
        1, current_metrics, regime, history, "BTC/USDT", "2023-01-01T00:00:00Z"
    )

    # We must then publish it to get the proposal object
    proposal = strategy_optimizer.publish_proposal(params, action)

    assert isinstance(proposal, OptimizerProposal)
    assert proposal.proposal_version == 1
    assert proposal.source == "StrategyOptimizer_v2"
    assert "min_score" in proposal.proposed_parameters
    assert proposal.context["action"] == action

    # Check if proposal was published to event bus
    published_proposal = event_bus_optimizer.subscribe_proposal()
    assert published_proposal.proposal_id == proposal.proposal_id


def test_placeholder(strategy_optimizer):
    # apply_frozen_epoch was removed or renamed in v2
    pass
