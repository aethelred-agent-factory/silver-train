
import json
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

class StateManager:
    """
    Manages the state of the optimizer using a SQLite database.
    """

    def __init__(self, config: Dict):
        
        if not isinstance(config, Dict):
            raise TypeError(f"Expected config to be a Dict, but got {type(config).__name__}")

        try:
            self.db_path = config["system_config"]["paths"]["state_db"]
        except KeyError as e:
            raise KeyError(f"Missing expected key in config: {e}")

        self._initialize_db()
        logging.info(f"Initialized StateManager with DB: {self.db_path}")

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        
        # In-memory DBs are exempt from directory checks
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimizer_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            conn.commit()

    def execute_query(self, query: str, params: tuple = (), fetch: Optional[str] = None) -> Any:
        """
        Executes a given SQL query and returns the results.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if fetch == "one":
                    return cursor.fetchone()
                if fetch == "all":
                    return cursor.fetchall()
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            raise

    def save_state(self, key: str, value: Any):
        
        serialized_value = json.dumps(value)
        self.execute_query("REPLACE INTO optimizer_state (key, value) VALUES (?, ?);", (key, serialized_value))

    def load_state(self, key: str) -> Any:
        
        result = self.execute_query("SELECT value FROM optimizer_state WHERE key = ?;", (key,), fetch="one")
        if result:
            return json.loads(result[0])
        return None
