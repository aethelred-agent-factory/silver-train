# tests/test_audit/test_audit_layer.py
from datetime import datetime, timezone

import pytest
from strategy_optimizer.audit.artifact_store import ArtifactStore
from strategy_optimizer.audit.audit_layer import AuditLayer
from strategy_optimizer.audit.causal_chain_validator import CausalChainValidator
from strategy_optimizer.audit.t1_checks import T1Checks
from strategy_optimizer.audit.t2_checks import T2Checks
from strategy_optimizer.audit.t3_checks import T3Checks
from strategy_optimizer.data_bus.event_bus import EventBus
from strategy_optimizer.data_bus.schemas import AuditAction, AuditVerdict, OptimizerProposal, TieredFinding


@pytest.fixture
def mock_t1_checks(mocker):
    mock = mocker.Mock(spec=T1Checks)
    mock.run_all.return_value = []
    return mock


@pytest.fixture
def mock_t2_checks(mocker):
    mock = mocker.Mock(spec=T2Checks)
    mock.run_all.return_value = []
    return mock


@pytest.fixture
def mock_t3_checks(mocker):
    mock = mocker.Mock(spec=T3Checks)
    mock.run_all.return_value = []
    return mock


@pytest.fixture
def mock_causal_validator(mocker):
    mock = mocker.Mock(spec=CausalChainValidator)
    mock.validate_proposal = mocker.Mock(return_value=True)
    return mock


@pytest.fixture
def mock_artifact_store(mocker):
    mock = mocker.Mock(spec=ArtifactStore)

    # store_artifact should preserve the verdict's action and just add artifact refs
    def store_artifact_side_effect(verdict: AuditVerdict):
        verdict.artifact_refs.append("file:///path/to/artifact")
        verdict.checksum = "dummy_checksum"
        return verdict

    mock.store_artifact.side_effect = store_artifact_side_effect
    mock.get_artifact_uri.return_value = "file:///path/to/artifact_id_123"
    return mock


@pytest.fixture
def event_bus_audit(in_memory_state_manager):
    return EventBus(in_memory_state_manager)


@pytest.fixture
def audit_layer(
    test_config,
    event_bus_audit,
    mock_t1_checks,
    mock_t2_checks,
    mock_t3_checks,
    mock_causal_validator,
    mock_artifact_store,
):
    return AuditLayer(
        test_config,
        event_bus_audit,
        mock_t1_checks,
        mock_t2_checks,
        mock_t3_checks,
        mock_causal_validator,
        mock_artifact_store,
    )


@pytest.fixture
def sample_proposal():
    return OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={
            "regime_label": "RANGE",
            "metrics_snapshot": {"atr_percentile_90": 0.5},
        },
        causal_chain_refs=[],
    )


def test_audit_proposal_allow(audit_layer, event_bus_audit, sample_proposal):
    verdict = audit_layer.audit_proposal(sample_proposal)

    assert isinstance(verdict, AuditVerdict)
    assert verdict.action.type == "ALLOW"
    assert not verdict.tiered_findings

    # Check if verdict was published
    published_verdict = event_bus_audit.subscribe_verdict()
    assert published_verdict == verdict


def test_audit_proposal_block_t1(
    audit_layer, event_bus_audit, mock_t1_checks, sample_proposal
):
    mock_t1_checks.run_all.return_value = [
        TieredFinding(
            tier="T1", code="T1_Contradiction", explanation="Contradiction found"
        )
    ]

    verdict = audit_layer.audit_proposal(sample_proposal)

    assert isinstance(verdict, AuditVerdict)
    assert verdict.action.type == "BLOCK"
    assert verdict.action.restrictions["reason"] == "T1_Contradiction"
    assert len(verdict.tiered_findings) == 1


def test_audit_proposal_restrict_t2(
    audit_layer, event_bus_audit, mock_t2_checks, sample_proposal
):
    mock_t2_checks.run_all.return_value = [
        TieredFinding(
            tier="T2", code="T2_InsufficientSample", explanation="Insufficient data"
        )
    ]

    verdict = audit_layer.audit_proposal(sample_proposal)

    assert isinstance(verdict, AuditVerdict)
    assert verdict.action.type == "ALLOW_WITH_RESTRICTION"
    assert verdict.action.restrictions["max_order_size_pct"] == 0.25
    assert len(verdict.tiered_findings) == 1
