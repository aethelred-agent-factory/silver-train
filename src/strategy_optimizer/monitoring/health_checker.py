import logging
import time

import requests  # For checking external APIs

# from storage.state_manager import StateManager
# from execution.exchange_adapter import ExchangeAdapter


class HealthChecker:
    """
    Monitors system health, checking database connectivity, API availability, etc.
    """

    def __init__(self, config, state_manager, exchange_adapter, alerting):
        self.config = config
        self.state_manager = state_manager
        self.exchange_adapter = exchange_adapter
        self.alerting = alerting
        self.health_check_interval = config["system_config"]["monitoring"][
            "health_check_interval"
        ]
        logging.info("Initialized HealthChecker.")

    def run_checks(self):
        """
        Runs all configured health checks.
        """
        logging.info("Running health checks...")
        all_healthy = True

        if not self._check_database_connection():
            all_healthy = False
            self.alerting.send_urgent_alert("Database connection failed!")

        if not self._check_exchange_api_connection():
            all_healthy = False
            self.alerting.send_urgent_alert("Exchange API connection failed!")

        # Add more checks as needed:
        # - Check disk space
        # - Check LLM API availability
        # - Check for excessive error logs

        if all_healthy:
            logging.info("All system health checks passed.")
        else:
            logging.warning("Some system health checks failed.")

        return all_healthy

    def _check_database_connection(self) -> bool:
        """
        Checks connectivity to the SQLite database.
        """
        try:
            # Attempt a simple query to verify connection
            self.state_manager.execute_query("SELECT 1;")
            return True
        except Exception as e:
            logging.error(f"Database connection check failed: {e}")
            return False

    def _check_exchange_api_connection(self) -> bool:
        """
        Checks connectivity to the configured exchange API.
        """
        try:
            # Use the exchange adapter to fetch some public data (e.g., time)
            # This is a lightweight way to check connectivity without authentication
            self.exchange_adapter.exchange.fetch_time()
            return True
        except Exception as e:
            logging.error(f"Exchange API connection check failed: {e}")
            return False

    def start_periodic_checks(self):
        """
        Starts a loop to run health checks periodically.
        This would typically run in a separate thread/process.
        """
        logging.info(
            f"Starting periodic health checks every {self.health_check_interval} seconds."
        )
        while True:
            self.run_checks()
            time.sleep(self.health_check_interval)
