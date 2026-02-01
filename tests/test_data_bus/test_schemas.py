# tests/test_data_bus/test_schemas.py
from datetime import datetime, timezone

import pytest
from strategy_optimizer.data_bus.schemas import (
    AuditAction,
    AuditVerdict,
    Candle,
    OptimizerProposal,
    TieredFinding,
)


def test_candle_schema():
    now = datetime.now(timezone.utc)
    candle = Candle(
        timestamp=now, open=100.0, high=105.0, low=98.0, close=103.0, volume=1000.0
    )
    assert isinstance(candle, Candle)
    assert candle.timestamp == now


def test_optimizer_proposal_schema():
    now = datetime.now(timezone.utc)
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test_optimizer",
        proposed_parameters={"param1": 1.0, "param2": "value"},
        context={"regime": "trend"},
        causal_chain_refs=[],
    )
    assert isinstance(proposal, OptimizerProposal)
    assert proposal.timestamp.date() == now.date()


def test_audit_verdict_schema():
    now = datetime.now(timezone.utc)
    finding = TieredFinding(
        tier="T1",
        code="T1_Test",
        explanation="Test finding",
        impact="Block execution",
        remediation="Fix param",
    )
    action = AuditAction(type="BLOCK", restrictions={"reason": "T1_Test"})
    verdict = AuditVerdict(
        proposal_id="test_proposal_id",
        tiered_findings=[finding],
        action=action,
        artifact_refs=["s3://test/artifact"],
        checksum="test_checksum",
    )
    assert isinstance(verdict, AuditVerdict)
    assert verdict.timestamp.date() == now.date()
