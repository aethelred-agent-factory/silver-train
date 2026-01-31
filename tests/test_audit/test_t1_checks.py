# tests/test_audit/test_t1_checks.py
from datetime import datetime

import pytest
from src.audit.t1_checks import T1Checks
from src.data_bus.schemas import OptimizerProposal, TieredFinding


@pytest.fixture
def t1_checks(test_config):
    return T1Checks(test_config)


@pytest.fixture
def sample_proposal_t1():
    return OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={
            "min_score": 2.0,
            "rsi_oversold": 30,
            "stop_multiplier": 2.5,
            "risk_pct": 0.5,
        },
        context={
            "regime_label": "RANGE",
            "metrics_snapshot": {"atr_percentile_90": 0.5},
        },
        causal_chain_refs=[],
    )


def test_check_contradiction_no_violation(t1_checks, sample_proposal_t1):
    finding = t1_checks.check_contradiction(sample_proposal_t1)
    assert finding is None


def test_check_contradiction_violation(t1_checks):
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"min_score": 2.0},
        context={
            "regime_label": "RANGE",
            "metrics_snapshot": {"atr_percentile_90": 0.95},
        },  # Contradiction
        causal_chain_refs=[],
    )
    finding = t1_checks.check_contradiction(proposal)
    assert finding is not None
    assert finding.tier == "T1"
    assert finding.code == "T1_Contradiction"


def test_check_bounds_no_violation(t1_checks, sample_proposal_t1):
    finding = t1_checks.check_bounds(sample_proposal_t1)
    assert finding is None


def test_check_bounds_violation(t1_checks):
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"min_score": -1.0},  # Out of bounds
        context={"regime_label": "TREND"},
        causal_chain_refs=[],
    )
    finding = t1_checks.check_bounds(proposal)
    assert finding is not None
    assert finding.tier == "T1"
    assert finding.code == "T1_BoundsViolation"


def test_run_all_t1_checks(t1_checks):
    proposal_with_violations = OptimizerProposal(
        proposal_version=101,
        source="test_optimizer",
        proposed_parameters={"min_score": -1.0},  # Bounds violation
        context={
            "regime_label": "RANGE",
            "metrics_snapshot": {"atr_percentile_90": 0.95},
        },  # Contradiction
        causal_chain_refs=[],
    )
    findings = t1_checks.run_all(proposal_with_violations)
    assert len(findings) == 3
    assert any(f.code == "T1_Contradiction" for f in findings)
    assert any(f.code == "T1_BoundsViolation" for f in findings)
    assert any(f.code == "T1_Circularity" for f in findings)
