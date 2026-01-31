# tests/test_audit/test_t2_checks.py
import pytest
from src.audit.t2_checks import T2Checks
from src.data_bus.schemas import OptimizerProposal, TieredFinding


@pytest.fixture
def t2_checks(test_config):
    return T2Checks(test_config)


@pytest.fixture
def sample_proposal_t2():
    return OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={
            "regime_label": "TREND",
            "metrics_snapshot": {"trades_sample": 150},
            "regime_confidence": 0.85,
        },
        causal_chain_refs=[{"type": "metric", "id": "metric_uuid_1"}],
    )


def test_check_insufficient_sample_no_violation(t2_checks, sample_proposal_t2):
    finding = t2_checks.check_insufficient_sample(sample_proposal_t2)
    assert finding is None


def test_check_insufficient_sample_violation(t2_checks):
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={
            "regime_label": "TREND",
            "metrics_snapshot": {"trades_sample": 50},  # Insufficient
        },
        causal_chain_refs=[{"type": "metric", "id": "metric_uuid_1"}],
    )
    finding = t2_checks.check_insufficient_sample(proposal)
    assert finding is not None
    assert finding.tier == "T2"
    assert finding.code == "T2_InsufficientSample"


def test_check_fuzzy_boundary_no_violation(t2_checks, sample_proposal_t2):
    finding = t2_checks.check_fuzzy_boundary(sample_proposal_t2)
    assert finding is None


def test_check_fuzzy_boundary_violation(t2_checks):
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={
            "regime_label": "TREND",
            "metrics_snapshot": {"trades_sample": 150},
            "regime_confidence": 0.6,  # Low confidence
        },
        causal_chain_refs=[{"type": "metric", "id": "metric_uuid_1"}],
    )
    finding = t2_checks.check_fuzzy_boundary(proposal)
    assert finding is not None
    assert finding.tier == "T2"
    assert finding.code == "T2_FuzzyBoundary"


def test_check_causal_gap_no_violation(t2_checks, sample_proposal_t2):
    finding = t2_checks.check_causal_gap(sample_proposal_t2)
    assert finding is None


def test_check_causal_gap_violation(t2_checks):
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={"regime_label": "TREND", "metrics_snapshot": {"trades_sample": 150}},
        causal_chain_refs=[],  # Missing causal chain
    )
    finding = t2_checks.check_causal_gap(proposal)
    assert finding is not None
    assert finding.tier == "T2"
    assert finding.code == "T2_CausalGap"


def test_run_all_t2_checks(t2_checks):
    proposal_with_violations = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={
            "regime_label": "TREND",
            "metrics_snapshot": {"trades_sample": 50},  # Insufficient Sample
            "regime_confidence": 0.6,  # Fuzzy Boundary
        },
        causal_chain_refs=[],  # Causal Gap
    )
    findings = t2_checks.run_all(proposal_with_violations)
    assert len(findings) == 3
    assert any(f.code == "T2_InsufficientSample" for f in findings)
    assert any(f.code == "T2_FuzzyBoundary" for f in findings)
    assert any(f.code == "T2_CausalGap" for f in findings)
