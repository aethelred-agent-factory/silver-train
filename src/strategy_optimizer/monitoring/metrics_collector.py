import logging

from backtesting.performance_metrics import PerformanceMetrics
from storage.interface import StorageInterface


class MetricsCollector:
    """
    Collects and stores various system metrics in the state database.
    """

    def __init__(self, storage: StorageInterface, performance_metrics: PerformanceMetrics):
        self.storage = storage
        self.performance_metrics = performance_metrics
        logging.info("Initialized MetricsCollector.")

    def collect_and_store(self):
        """
        Collects metrics from various components and stores them.
        """
        metrics = {
            "performance": self.performance_metrics.get_all_metrics(),
            # Add other metrics here (e.g., from IncidentTracker, OrderManager)
        }

        for key, value in metrics.items():
            self.storage.save_state(f"metrics_{key}", value)

        logging.info("Collected and stored system metrics.")

    def get_metrics(self, key: str) -> dict:
        """
        Retrieves a specific set of metrics from the database.
        """
        return self.storage.load_state(f"metrics_{key}")
