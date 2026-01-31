import sqlite3
import logging
from threading import Lock

class StateManager:
    """
    Manages the SQLite WAL database interface for persistent state.
    """
    def __init__(self, config):
        self.config = config
        self.db_path = config['system_config']['paths']['state_db']
        self._connection_lock = Lock()
        self._initialize_db()
        logging.info(f"Initialized StateManager with DB: {self.db_path}")

    def _get_connection(self):
        """Internal method to get a thread-safe database connection."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _initialize_db(self):
        """Ensures the database file and basic schema exist."""
        with self._connection_lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                # Example table creation (can be more comprehensive based on needs)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS optimizer_state (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                """)
                conn.commit()
            except Exception as e:
                logging.error(f"Error initializing database: {e}")
                conn.rollback()
            finally:
                conn.close()

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
        with self._connection_lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                return None
            except Exception as e:
                logging.error(f"Error executing query '{query}' with params {params}: {e}")
                conn.rollback()
                raise
            finally:
                conn.close()

    def save_state(self, key: str, value: str):
        """Saves a key-value pair to the optimizer state table."""
        query = "REPLACE INTO optimizer_state (key, value) VALUES (?, ?);"
        self.execute_query(query, (key, value))
        logging.debug(f"State saved: {key}")

    def load_state(self, key: str) -> str:
        """Loads a value by key from the optimizer state table."""
        query = "SELECT value FROM optimizer_state WHERE key = ?;"
        result = self.execute_query(query, (key,), fetch='one')
        logging.debug(f"State loaded for {key}")
        return result[0] if result else None
