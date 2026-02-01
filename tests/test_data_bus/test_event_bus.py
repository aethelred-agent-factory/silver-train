# tests/test_data_bus/test_event_bus.py
from datetime import datetime, timezone

import pytest
from data_bus.event_bus import EventBus
from data_bus.schemas import (
    AuditAction,
    AuditVerdict,
    OptimizerProposal,
    TieredFinding,
)


def test_publish_and_subscribe_proposal(in_memory_state_manager):
    event_bus = EventBus(in_memory_state_manager)
    proposal = OptimizerProposal(
        proposal_version=1,
        source="test",
        proposed_parameters={"p1": 1},
        context={},
        causal_chain_refs=[],
    )
    event_bus.publish_proposal(proposal)
    retrieved_proposal = event_bus.subscribe_proposal()
    assert retrieved_proposal == proposal
    assert event_bus.subscribe_proposal() is None


def test_publish_and_subscribe_verdict(in_memory_state_manager):
    event_bus = EventBus(in_memory_state_manager)
    verdict = AuditVerdict(
        proposal_id="test_prop",
        tiered_findings=[],
        action=AuditAction(type="ALLOW"),
        artifact_refs=[],
        checksum="abc",
    )
    event_bus.publish_verdict(verdict)
    retrieved_verdict = event_bus.subscribe_verdict("test_prop")
    assert retrieved_verdict == verdict
    assert event_bus.subscribe_verdict("test_prop") is None
