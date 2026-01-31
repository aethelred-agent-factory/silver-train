import logging
from prometheus_client import Gauge, Counter, generate_latest

class MetricsCollector:
    """
    Collects Prometheus-style metrics from the application.
    """
    def __init__(self):
        # Gauges for current state
        self.equity_gauge = Gauge('optimizer_equity_usd', 'Current equity in USD')
        self.drawdown_gauge = Gauge('optimizer_drawdown_pct', 'Current maximum drawdown percentage')
        self.active_positions_gauge = Gauge('optimizer_active_positions', 'Number of currently open positions')

        # Counters for events
        self.proposals_total = Counter('optimizer_proposals_total', 'Total number of optimizer proposals')
        self.audit_t1_failures_total = Counter('audit_t1_failures_total', 'Total T1 audit failures')
        self.audit_t2_flags_total = Counter('audit_t2_flags_total', 'Total T2 audit flags')
        self.audit_t3_gaps_total = Counter('audit_t3_gaps_total', 'Total T3 audit informational gaps')
        self.trades_executed_total = Counter('optimizer_trades_executed_total', 'Total trades executed')
        self.emergency_halts_total = Counter('governance_emergency_halts_total', 'Total emergency system halts')
        
        logging.info("Initialized MetricsCollector.")

    def update_equity(self, equity: float):
        self.equity_gauge.set(equity)

    def update_drawdown(self, drawdown: float):
        self.drawdown_gauge.set(drawdown)

    def update_active_positions(self, count: int):
        self.active_positions_gauge.set(count)

    def increment_proposals(self):
        self.proposals_total.inc()

    def increment_audit_t1_failures(self):
        self.audit_t1_failures_total.inc()

    def increment_audit_t2_flags(self):
        self.audit_t2_flags_total.inc()

    def increment_audit_t3_gaps(self):
        self.audit_t3_gaps_total.inc()

    def increment_trades_executed(self):
        self.trades_executed_total.inc()

    def increment_emergency_halts(self):
        self.emergency_halts_total.inc()

    def generate_prometheus_metrics(self) -> bytes:
        """
        Generates the Prometheus metrics in the exposition format.
        """
        return generate_latest()
