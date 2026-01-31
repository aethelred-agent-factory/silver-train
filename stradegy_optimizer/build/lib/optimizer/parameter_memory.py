import logging
import json

class ParameterMemory:
    """
    Tracks tested parameter combinations to prevent repetition.
    Uses the state_manager (SQLite) for persistence.
    """
    def __init__(self, state_manager):
        self.state_manager = state_manager
        # Ensure the table exists
        self.state_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS parameter_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                params_hash TEXT NOT NULL,
                regime TEXT NOT NULL,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logging.info("Initialized ParameterMemory.")

    def log_tested(self, params: dict, regime: str, result: str):
        """
        Logs a tested parameter combination to the database.
        """
        params_hash = self._hash_params(params)
        logging.info(f"Logging tested parameters for regime '{regime}' with hash {params_hash}")
        
        query = "INSERT INTO parameter_history (params_hash, regime, result) VALUES (?, ?, ?)"
        self.state_manager.execute_query(query, (params_hash, regime, result))

    def has_been_tested(self, params: dict, regime: str) -> bool:
        """
        Checks if a parameter combination has been tested before in a given regime.
        """
        params_hash = self._hash_params(params)
        logging.info(f"Checking if parameters have been tested for regime '{regime}' with hash {params_hash}")
        
        query = "SELECT 1 FROM parameter_history WHERE params_hash = ? AND regime = ?"
        result = self.state_manager.execute_query(query, (params_hash, regime), fetch='one')
        
        return result is not None

    def _hash_params(self, params: dict) -> str:
        """
        Creates a deterministic hash of the parameters dictionary.
        """
        # Sort the dictionary by key to ensure consistent hash
        sorted_params = json.dumps(params, sort_keys=True)
        return str(hash(sorted_params))
