import logging

from backtesting.performance_metrics import PerformanceMetrics
from storage.state_manager import StateManager


class MetricsCollector:
    """
    Collects and exposes real-time metrics for the dashboard.
    """

    def __init__(
        self, state_manager: StateManager, performance_metrics: PerformanceMetrics
    ):
        self.state_manager = state_manager
        self.performance_metrics = performance_metrics
        logging.info("Initialized MetricsCollector.")

    def get_latest_metrics(self):
        """
        Retrieves the latest performance metrics from the backtest reports.
        """
        query = "SELECT report FROM backtest_reports ORDER BY end_date DESC LIMIT 1"
        result = self.state_manager.execute_query(query, fetch="one")
        if result and result[0]:
            # The report is stored as a JSON string
            return self.performance_metrics.parse_report(result[0])
        return {}
