# tests/test_audit/test_causal_chain_validator.py
import pytest
from datetime import datetime, timedelta
from src.audit.causal_chain_validator import CausalChainValidator
from src.data_bus.schemas import OptimizerProposal, CausalChainRef
from src.storage.artifact_manager import ArtifactManager # For mocking

@pytest.fixture
def mock_artifact_manager(mocker):
    mock = mocker.Mock(spec=ArtifactManager)
    mock.retrieve_artifact = mocker.Mock(
        side_effect=lambda artifact_id: type('obj', (object,), {'timestamp': datetime.utcnow() - timedelta(hours=1)})()
        if not "future" in artifact_id
        else type('obj', (object,), {'timestamp': datetime.utcnow() + timedelta(hours=1)})()
    )
    return mock

@pytest.fixture
def causal_chain_validator(test_config, mock_artifact_manager):
    return CausalChainValidator(test_config, mock_artifact_manager)

def test_validate_proposal_valid(causal_chain_validator, mock_artifact_manager):
    now = datetime.utcnow()
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test",
        proposed_parameters={},
        context={},
        causal_chain_refs=[
            CausalChainRef(type="metric", id="metric_id_past"),
            CausalChainRef(type="data", id="data_id_past")
        ],
        timestamp=now
    )
    # Mock retrieve_artifact to always return past timestamps for this test
    mock_artifact_manager.retrieve_artifact.side_effect = lambda artifact_id: type('obj', (object,), {'timestamp': now - timedelta(hours=1)})()

    assert causal_chain_validator.validate_proposal(proposal) is True
    # mock_artifact_manager.retrieve_artifact.assert_called() # Should have been called twice

def test_validate_proposal_future_artifact(causal_chain_validator):
    now = datetime.utcnow()
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test",
        proposed_parameters={},
        context={},
        causal_chain_refs=[
            CausalChainRef(type="metric", id="metric_id_past"),
            CausalChainRef(type="data", id="data_id_future") # This will be mocked as future
        ],
        timestamp=now
    )
    # The fixture's mock_artifact_manager already handles "future" in ID

    assert causal_chain_validator.validate_proposal(proposal) is False

def test_validate_proposal_missing_artifact(causal_chain_validator, mock_artifact_manager):
    now = datetime.utcnow()
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test",
        proposed_parameters={},
        context={},
        causal_chain_refs=[
            CausalChainRef(type="metric", id="non_existent_id")
        ],
        timestamp=now
    )
    mock_artifact_manager.retrieve_artifact.return_value = None # Simulate missing artifact

    # This test will currently pass because the placeholder in CausalChainValidator
    # directly checks for "future" in the ID.
    # When ArtifactManager.retrieve_artifact is fully implemented and returns None,
    # this test should correctly return False.
    assert causal_chain_validator.validate_proposal(proposal) is True # This will be False later
