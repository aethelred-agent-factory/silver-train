# tests/test_storage/test_replay_engine.py
import pytest
from datetime import datetime, timezone, timedelta
from src.storage.replay_engine import ReplayEngine
from src.storage.artifact_manager import ArtifactManager
from src.optimizer.strategy_optimizer import StrategyOptimizer
from src.data_bus.schemas import OptimizerProposal, AuditVerdict, AuditAction, TieredFinding

@pytest.fixture
def mock_artifact_manager(mocker):
    mock = mocker.Mock(spec=ArtifactManager)
    # Mock download_artifact to return a sample AuditVerdict JSON
    sample_verdict_json = AuditVerdict(
        audit_id="test_audit_id_123",
        proposal_id="test_proposal_id_123",
        timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
        tiered_findings=[],
        action=AuditAction(type="ALLOW"),
        artifact_refs=["file:///some/artifact.json"],
        checksum="abc"
    ).model_dump_json()
    mock.download_artifact.return_value = sample_verdict_json
    mock.get_artifact_uri.return_value = "file:///mock/path/artifact.json"
    return mock

@pytest.fixture
def mock_strategy_optimizer(mocker):
    mock = mocker.Mock(spec=StrategyOptimizer)
    # Mock propose_parameters to return a deterministic proposal
    mock.propose_parameters.return_value = OptimizerProposal(
        proposal_version=2,
        source="replayed_optimizer_v1",
        proposed_parameters={"min_score": 2.5},
        context={"regime_label": "TREND"},
        causal_chain_refs=[]
    )
    return mock

@pytest.fixture
def replay_engine(test_config, mock_artifact_manager, mock_strategy_optimizer):
    return ReplayEngine(test_config, mock_artifact_manager, mock_strategy_optimizer)

def test_replay_decision(replay_engine, mock_artifact_manager):
    proposal_id = "test_proposal_id_123"
    replayed_decision = replay_engine.replay_decision(proposal_id)
    
    assert replayed_decision is not None
    assert replayed_decision['proposal_id'] == proposal_id
    
    # mock_artifact_manager.download_artifact.assert_called_once_with(f"audit_{proposal_id}.json")
    # mock_strategy_optimizer.propose_parameters.assert_called_once() # Will be called once uncommented

def test_verify_reproducibility_success(replay_engine):
    original_proposal_id = "test_proposal_id_123"
    replayed_result = {"proposal_id": "test_proposal_id_123", "param1": 10} # Simplified result
    
    is_reproducible = replay_engine.verify_reproducibility(original_proposal_id, replayed_result)
    assert is_reproducible is True

def test_verify_reproducibility_failure(replay_engine):
    original_proposal_id = "test_proposal_id_123"
    replayed_result = {"proposal_id": "different_proposal_id", "param1": 10} # Mismatched ID
    
    is_reproducible = replay_engine.verify_reproducibility(original_proposal_id, replayed_result)
    assert is_reproducible is False
