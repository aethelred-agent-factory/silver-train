import json
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd

from .interface import StorageInterface

class SqliteStorage(StorageInterface):
    """
    Storage implementation for SQLite and local filesystem.
    This class is a wrapper around the existing data access logic.
    """

    def __init__(self, db_path: str, artifacts_path: str, market_data_path: str):
        self.db_path = db_path
        self.artifacts_path = artifacts_path
        self.market_data_path = market_data_path
        self._memory_conn = None

        # Ensure directories exist
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        else:
            # For in-memory database, we must keep one connection open
            self._memory_conn = sqlite3.connect(self.db_path, check_same_thread=False)

        os.makedirs(self.artifacts_path, exist_ok=True)
        os.makedirs(self.market_data_path, exist_ok=True)

        self._initialize_db()
        logging.info(f"Initialized SqliteStorage with DB: {self.db_path}")

    def _get_connection(self):
        if self._memory_conn:
            return self._memory_conn
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS optimizer_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        conn.commit()
        # If not in-memory, we can close it (it's called in __init__)
        if not self._memory_conn:
            conn.close()

    def save_state(self, key: str, value: Dict) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "REPLACE INTO optimizer_state (key, value) VALUES (?, ?);",
                (key, json.dumps(value)),
            )
            conn.commit()
            if not self._memory_conn:
                conn.close()
            logging.debug(f"State saved: {key}")
            return True
        except Exception as e:
            logging.error(f"Error saving state: {e}")
            return False

    def load_state(self, key: str) -> Optional[Dict]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM optimizer_state WHERE key = ?;", (key,))
            result = cursor.fetchone()
            if not self._memory_conn:
                conn.close()

            if result:
                logging.debug(f"State loaded for {key}")
                return json.loads(result[0])
            return None
        except Exception as e:
            logging.error(f"Error loading state: {e}")
            return None

    def delete_state(self, key: str) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM optimizer_state WHERE key = ?;", (key,))
            conn.commit()
            if not self._memory_conn:
                conn.close()
            logging.debug(f"State deleted for {key}")
            return True
        except Exception as e:
            logging.error(f"Error deleting state: {e}")
            return False

    def save_artifact(self, artifact_id: str, content: Dict, checksum: str) -> bool:
        try:
            filepath = os.path.join(self.artifacts_path, artifact_id)
            content_str = json.dumps(content, indent=4)
            with open(filepath, "w") as f:
                f.write(content_str)
            with open(filepath + ".sha256", "w") as f:
                f.write(checksum)
            logging.info(f"Artifact {artifact_id} saved to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error saving artifact: {e}")
            return False

    def load_artifact(self, artifact_id: str) -> Optional[Dict]:
        try:
            filepath = os.path.join(self.artifacts_path, artifact_id)
            if not os.path.exists(filepath):
                return None
            with open(filepath, "r") as f:
                content = f.read()
            return json.loads(content)
        except Exception as e:
            logging.error(f"Error loading artifact: {e}")
            return None

    def execute_query(self, query: str, params: tuple = (), fetch: Optional[str] = None) -> Any:
        """
        Executes a given SQL query and returns the results.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = None
            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            else:
                conn.commit()

            if not self._memory_conn:
                conn.close()
            return result
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            raise

    def save_market_data(self, symbol: str, df: pd.DataFrame) -> bool:
        try:
            safe_symbol = symbol.replace("/", "_")
            os.makedirs(self.market_data_path, exist_ok=True)
            filepath = os.path.join(self.market_data_path, f"{safe_symbol}.parquet")

            if os.path.exists(filepath):
                try:
                    existing_df = pd.read_parquet(filepath)
                    df = pd.concat([existing_df, df]).drop_duplicates().reset_index(drop=True)
                except Exception:
                    pass # Just overwrite if read fails

            df.to_parquet(filepath, index=False)
            return True
        except Exception as e:
            logging.error(f"Error saving market data: {e}")
            return False

    def query_market_data(self, symbol: str, start: str, end: str) -> List[Dict]:
        try:
            safe_symbol = symbol.replace("/", "_")
            filepath = os.path.join(self.market_data_path, f"{safe_symbol}.parquet")

            if not os.path.exists(filepath):
                return []

            df = pd.read_parquet(filepath)

            if df.empty:
                return []

            # Filter by symbol and date range
            if "symbol" in df.columns:
                df = df[df["symbol"] == symbol]

            if "timestamp" in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                if start:
                    start_dt = pd.to_datetime(start, utc=True)
                    df = df[df["timestamp"] >= start_dt]
                if end:
                    end_dt = pd.to_datetime(end, utc=True)
                    df = df[df["timestamp"] <= end_dt]

            return df.to_dict("records")
        except Exception as e:
            logging.error(f"Error querying market data: {e}")
            return []
