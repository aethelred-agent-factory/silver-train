# tests/test_audit/test_t3_checks.py
import pytest
from strategy_optimizer.audit.t3_checks import T3Checks
from strategy_optimizer.data_bus.schemas import OptimizerProposal, TieredFinding


@pytest.fixture
def t3_checks(test_config):
    # Temporarily remove 'liquidity_thresholds' from config for testing config_gaps
    original_config = test_config.copy()
    if "liquidity_thresholds" in test_config:
        del test_config["liquidity_thresholds"]
    yield T3Checks(test_config)
    # Restore original config
    test_config.update(original_config)


@pytest.fixture
def sample_proposal_t3():
    return OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={"regime_label": "TREND", "metrics_snapshot": {"trades_sample": 150}},
        causal_chain_refs=[],
    )


def test_check_config_gaps_violation(t3_checks, sample_proposal_t3):
    # This test assumes 'liquidity_thresholds' is NOT in the test_config fixture
    finding = t3_checks.check_config_gaps(sample_proposal_t3)
    assert finding is not None
    assert finding.tier == "T3"
    assert finding.code == "T3_ConfigGap"


def test_check_ambiguous_logs_no_violation(t3_checks, sample_proposal_t3):
    finding = t3_checks.check_ambiguous_logs(sample_proposal_t3)
    assert finding is None


def test_check_ambiguous_logs_violation(t3_checks):
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={
            "regime_label": "TREND",
            "metrics_snapshot": {"trades_sample": 150},
            "has_ambiguous_logs": True,  # Flag to simulate ambiguous logs
        },
        causal_chain_refs=[],
    )
    finding = t3_checks.check_ambiguous_logs(proposal)
    assert finding is not None
    assert finding.tier == "T3"
    assert finding.code == "T3_Ambiguity"


def test_run_all_t3_checks(t3_checks):
    proposal_with_violations = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0},
        context={
            "regime_label": "TREND",
            "metrics_snapshot": {"trades_sample": 150},
            "has_ambiguous_logs": True,  # Ambiguous logs
        },
        causal_chain_refs=[],
    )
    # Note: test_config is manipulated in the fixture to trigger config_gaps
    findings = t3_checks.run_all(proposal_with_violations)
    assert len(findings) == 2
    assert any(f.code == "T3_ConfigGap" for f in findings)
    assert any(f.code == "T3_Ambiguity" for f in findings)
