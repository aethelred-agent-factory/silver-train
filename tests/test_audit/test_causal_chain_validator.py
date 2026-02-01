# tests/test_audit/test_causal_chain_validator.py
from datetime import datetime, timedelta

import pytest
from audit.causal_chain_validator import CausalChainValidator
from data_bus.schemas import CausalChainRef, OptimizerProposal
from storage.interface import StorageInterface


@pytest.fixture
def mock_artifact_manager(mocker):
    mock = mocker.Mock(spec=StorageInterface)
    mock.load_artifact.side_effect = lambda artifact_id: {
        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
    } if not "future" in artifact_id else {
        "timestamp": (datetime.now() + timedelta(hours=1)).isoformat()
    }
    return mock


@pytest.fixture
def causal_chain_validator(test_config, mock_artifact_manager):
    return CausalChainValidator(test_config, mock_artifact_manager)


def test_validate_proposal_valid(causal_chain_validator, mock_artifact_manager):
    now = datetime.now()
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test",
        proposed_parameters={},
        context={},
        causal_chain_refs=[
            CausalChainRef(type="metric", id="metric_id_past"),
            CausalChainRef(type="data", id="data_id_past"),
        ],
        timestamp=now,
    )
    # Mock load_artifact to always return past timestamps for this test
    mock_artifact_manager.load_artifact.side_effect = lambda artifact_id: {
        "timestamp": (now - timedelta(hours=1)).isoformat()
    }

    assert causal_chain_validator.validate_proposal(proposal) is True
    # mock_artifact_manager.retrieve_artifact.assert_called() # Should have been called twice


def test_validate_proposal_future_artifact(causal_chain_validator):
    now = datetime.now()
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test",
        proposed_parameters={},
        context={},
        causal_chain_refs=[
            CausalChainRef(type="metric", id="metric_id_past"),
            CausalChainRef(
                type="data", id="data_id_future"
            ),  # This will be mocked as future
        ],
        timestamp=now,
    )
    # The fixture's mock_artifact_manager already handles "future" in ID

    assert causal_chain_validator.validate_proposal(proposal) is False


def test_validate_proposal_missing_artifact(
    causal_chain_validator, mock_artifact_manager
):
    now = datetime.now()
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test",
        proposed_parameters={},
        context={},
        causal_chain_refs=[CausalChainRef(type="metric", id="non_existent_id")],
        timestamp=now,
    )
    mock_artifact_manager.load_artifact.side_effect = None
    mock_artifact_manager.load_artifact.return_value = (
        None  # Simulate missing artifact
    )

    assert causal_chain_validator.validate_proposal(proposal) is False
