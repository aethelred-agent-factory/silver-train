import logging
import sqlite3
from threading import Lock

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool


class StateManager:
    """
    Manages the SQLite WAL database interface for persistent state.
    """

    def __init__(self, config):
        self.config = config
        self.db_path = config["system_config"]["paths"]["state_db"]
        self._connection_lock = Lock()
        if self.db_path == ":memory:":
            self.engine = create_engine(
                "sqlite:///:memory:",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(
                f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False}
            )

        self._initialize_db()
        logging.info(f"Initialized StateManager with DB: {self.db_path}")

    def _get_connection(self):
        """Internal method to get a thread-safe database connection."""
        return self.engine.connect()

    def _initialize_db(self):
        """Ensures the database file and basic schema exist."""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS optimizer_state (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                """
                    )
                )
                conn.commit()
            except Exception as e:
                logging.error(f"Error initializing database: {e}")
                conn.rollback()

    def execute_query(self, query: str, params: tuple = (), fetch: str = None):
        """
        Executes a SQL query.

        Args:
            query: The SQL query string.
            params: Parameters for the query.
            fetch: 'one' to fetch one row, 'all' to fetch all rows, None for no fetch (e.g., INSERT, UPDATE).

        Returns:
            Fetched data if 'fetch' is specified, otherwise None.
        """
        with self._get_connection() as conn:
            try:
                # Create a dictionary of parameters
                params_dict = {f"p{i+1}": v for i, v in enumerate(params)}

                # Replace '?' with ':p1', ':p2', etc.
                for i in range(len(params)):
                    query = query.replace("?", f":p{i+1}", 1)

                result = conn.execute(text(query), params_dict)
                conn.commit()
                if fetch == "one":
                    return result.fetchone()
                elif fetch == "all":
                    return result.fetchall()
                return None
            except Exception as e:
                logging.error(
                    f"Error executing query '{query}' with params {params}: {e}"
                )
                conn.rollback()
                raise

    def save_state(self, key: str, value: str):
        """Saves a key-value pair to the optimizer state table."""
        query = "REPLACE INTO optimizer_state (key, value) VALUES (?, ?);"
        self.execute_query(query, (key, value))
        logging.debug(f"State saved: {key}")

    def load_state(self, key: str) -> str:
        """Loads a value by key from the optimizer state table."""
        query = "SELECT value FROM optimizer_state WHERE key = ?;"
        result = self.execute_query(query, (key,), fetch="one")
        logging.debug(f"State loaded for {key}")
        return result[0] if result else None

    def is_kill_switch_active(self) -> bool:
        """
        Checks if the global kill switch has been activated in the database.
        This is the source of truth for emergency halts.
        """
        try:
            val = self.load_state("GLOBAL_KILL_SWITCH")
            return val == "HALTED"
        except Exception:
            # On error, fail closed (assume halted)
            return True
