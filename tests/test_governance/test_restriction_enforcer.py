# tests/test_governance/test_restriction_enforcer.py
import pytest
from src.data_bus.schemas import AuditAction, AuditVerdict
from src.governance.restriction_enforcer import RestrictionEnforcer


@pytest.fixture
def restriction_enforcer(test_config):
    return RestrictionEnforcer(test_config)


def test_apply_restrictions(restriction_enforcer):
    audit_verdict = AuditVerdict(
        action=AuditAction(
            type="ALLOW_WITH_RESTRICTION",
            restrictions={"max_order_size_pct": 0.5, "max_daily_trades": 10},
        )
    )
    restriction_enforcer.apply_restrictions(audit_verdict)

    active_restrictions = restriction_enforcer.get_active_restrictions()
    assert active_restrictions == {"max_order_size_pct": 0.5, "max_daily_trades": 10}


def test_apply_restrictions_no_restriction_type(restriction_enforcer):
    audit_verdict = AuditVerdict(action=AuditAction(type="ALLOW"))
    restriction_enforcer.apply_restrictions(audit_verdict)
    assert restriction_enforcer.get_active_restrictions() == {}


def test_apply_restrictions_override(restriction_enforcer):
    audit_verdict1 = AuditVerdict(
        action=AuditAction(
            type="ALLOW_WITH_RESTRICTION", restrictions={"max_order_size_pct": 0.5}
        )
    )
    restriction_enforcer.apply_restrictions(audit_verdict1)
    assert restriction_enforcer.get_active_restrictions() == {"max_order_size_pct": 0.5}

    audit_verdict2 = AuditVerdict(
        action=AuditAction(
            type="ALLOW_WITH_RESTRICTION",
            restrictions={"max_order_size_pct": 0.25, "new_restriction": True},
        )
    )
    restriction_enforcer.apply_restrictions(audit_verdict2)
    assert restriction_enforcer.get_active_restrictions() == {
        "max_order_size_pct": 0.25,
        "new_restriction": True,
    }


def test_lift_restrictions(restriction_enforcer):
    # First apply some restrictions
    audit_verdict_apply = AuditVerdict(
        action=AuditAction(
            type="ALLOW_WITH_RESTRICTION",
            restrictions={"max_order_size_pct": 0.5, "max_daily_trades": 10},
        )
    )
    restriction_enforcer.apply_restrictions(audit_verdict_apply)
    assert restriction_enforcer.get_active_restrictions() == {
        "max_order_size_pct": 0.5,
        "max_daily_trades": 10,
    }

    # Now lift one restriction
    audit_verdict_lift = AuditVerdict(
        action=AuditAction(
            type="RESTRICTION_LIFTED",
            restrictions={"max_order_size_pct": None},  # Value doesn't matter, just key
        )
    )
    restriction_enforcer.lift_restrictions(audit_verdict_lift)
    assert restriction_enforcer.get_active_restrictions() == {"max_daily_trades": 10}

    # Lift all if no specific restriction is mentioned
    audit_verdict_lift_all = AuditVerdict(action=AuditAction(type="RESTRICTION_LIFTED"))
    restriction_enforcer.lift_restrictions(audit_verdict_lift_all)
    assert restriction_enforcer.get_active_restrictions() == {}
