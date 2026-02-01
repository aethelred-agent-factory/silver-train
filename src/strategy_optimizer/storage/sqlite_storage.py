import json
import logging
import os
import sqlite3
from typing import Dict, List, Optional
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
        os.makedirs(self.artifacts_path, exist_ok=True)
        self._initialize_db()
        logging.info(f"Initialized SqliteStorage with DB: {self.db_path}")

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        with self._get_connection() as conn:
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

    def save_state(self, key: str, value: Dict) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "REPLACE INTO optimizer_state (key, value) VALUES (?, ?);",
                    (key, json.dumps(value)),
                )
                conn.commit()
            logging.debug(f"State saved: {key}")
            return True
        except Exception as e:
            logging.error(f"Error saving state: {e}")
            return False

    def load_state(self, key: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM optimizer_state WHERE key = ?;", (key,))
                result = cursor.fetchone()
            if result:
                logging.debug(f"State loaded for {key}")
                return json.loads(result[0])
            return None
        except Exception as e:
            logging.error(f"Error loading state: {e}")
            return None

    def delete_state(self, key: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM optimizer_state WHERE key = ?;", (key,))
                conn.commit()
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

    def query_market_data(self, symbol: str, start: str, end: str) -> List[Dict]:
        try:
            # Assuming market data is stored in a single parquet file for simplicity
            # A more robust implementation would handle multiple files and formats.
            files = [f for f in os.listdir(self.market_data_path) if f.endswith('.parquet')]
            if not files:
                logging.error("No market data files found.")
                return []

            # Load the first parquet file found
            file_path = os.path.join(self.market_data_path, files[0])
            df = pd.read_parquet(file_path)

            # Filter by symbol and date range
            df['time'] = pd.to_datetime(df['time'])
            mask = (
                (df["symbol"] == symbol) &
                (df["time"] >= pd.to_datetime(start)) &
                (dest["time"] <= pd.to_datetime(end))
            )
            filtered_df = df.loc[mask]

            return filtered_df.to_dict("records")
        except Exception as e:
            logging.error(f"Error querying market data: {e}")
            return []
