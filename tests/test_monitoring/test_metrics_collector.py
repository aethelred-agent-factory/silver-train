# tests/test_monitoring/test_metrics_collector.py
import pytest
from prometheus_client import generate_latest
from src.monitoring.metrics_collector import MetricsCollector


@pytest.fixture
def metrics_collector():
    # Resetting metrics before each test to ensure isolation
    # This is a bit hacky, but necessary for Prometheus client tests
    from prometheus_client import REGISTRY

    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    return MetricsCollector()


def test_update_equity(metrics_collector):
    metrics_collector.update_equity(100000.50)
    metrics = generate_latest().decode()
    assert "optimizer_equity_usd 100000.5" in metrics


def test_update_drawdown(metrics_collector):
    metrics_collector.update_drawdown(5.25)
    metrics = generate_latest().decode()
    assert "optimizer_drawdown_pct 5.25" in metrics


def test_increment_proposals(metrics_collector):
    metrics_collector.increment_proposals()
    metrics_collector.increment_proposals()
    metrics = generate_latest().decode()
    assert "optimizer_proposals_total 2.0" in metrics


def test_increment_audit_t1_failures(metrics_collector):
    metrics_collector.increment_audit_t1_failures()
    metrics = generate_latest().decode()
    assert "audit_t1_failures_total 1.0" in metrics


def test_generate_prometheus_metrics(metrics_collector):
    metrics_collector.update_equity(1234.5)
    metrics_collector.increment_proposals()

    generated = metrics_collector.generate_prometheus_metrics()
    decoded = generated.decode()

    assert "optimizer_equity_usd 1234.5" in decoded
    assert "optimizer_proposals_total 1.0" in decoded
    assert "# HELP optimizer_equity_usd Current equity in USD" in decoded
