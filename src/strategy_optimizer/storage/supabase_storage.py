import json
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from supabase import create_client, Client

from .interface import StorageInterface

class SupabaseStorage(StorageInterface):
    """
    Storage implementation for Supabase (Postgres, Storage, and Realtime).
    """

    def __init__(self, url: str, key: str, bucket_name: str = "artifacts"):
        self.url = url
        self.key = key
        self.bucket_name = bucket_name
        self.client: Client = create_client(self.url, self.key)
        logging.info(f"Initialized SupabaseStorage at {self.url}")

    def save_state(self, key: str, value: Dict) -> bool:
        try:
            # Using upsert (on_conflict do update)
            data = {"key": key, "value": value}
            self.client.table("optimizer_state").upsert(data).execute()
            logging.debug(f"State saved to Supabase: {key}")
            return True
        except Exception as e:
            logging.error(f"Error saving state to Supabase: {e}")
            return False

    def load_state(self, key: str) -> Optional[Dict]:
        try:
            response = self.client.table("optimizer_state").select("value").eq("key", key).execute()
            if response.data:
                logging.debug(f"State loaded from Supabase for {key}")
                return response.data[0]["value"]
            return None
        except Exception as e:
            logging.error(f"Error loading state from Supabase: {e}")
            return None

    def delete_state(self, key: str) -> bool:
        try:
            self.client.table("optimizer_state").delete().eq("key", key).execute()
            logging.debug(f"State deleted from Supabase for {key}")
            return True
        except Exception as e:
            logging.error(f"Error deleting state from Supabase: {e}")
            return False

    def save_artifact(self, artifact_id: str, content: Dict, checksum: str) -> bool:
        try:
            # 1. Upload content to Supabase Storage
            content_str = json.dumps(content, indent=4)
            content_bytes = content_str.encode("utf-8")

            # Storage path: bucket/artifact_id
            self.client.storage.from_(self.bucket_name).upload(
                path=artifact_id,
                file=content_bytes,
                file_options={"content-type": "application/json", "upsert": "true"}
            )

            # 2. Get public URL (or just construct URI)
            uri = f"supabase://{self.bucket_name}/{artifact_id}"

            # 3. Save metadata to Postgres
            metadata = {
                "id": artifact_id,
                "checksum": checksum,
                "uri": uri
            }
            self.client.table("artifacts").upsert(metadata).execute()

            logging.info(f"Artifact {artifact_id} saved to Supabase Storage and metadata to DB")
            return True
        except Exception as e:
            logging.error(f"Error saving artifact to Supabase: {e}")
            return False

    def load_artifact(self, artifact_id: str) -> Optional[Dict]:
        try:
            # 1. Download from Supabase Storage
            response = self.client.storage.from_(self.bucket_name).download(artifact_id)
            if response:
                return json.loads(response)
            return None
        except Exception as e:
            logging.error(f"Error loading artifact from Supabase: {e}")
            return None

    def execute_query(self, query: str, params: tuple = (), fetch: Optional[str] = None) -> Any:
        """
        Placeholder for execute_query.
        Note: Supabase backend uses PostgREST and doesn't support raw SQL strings easily.
        """
        logging.warning("execute_query is not fully supported in SupabaseStorage yet.")
        return None

    def save_market_data(self, symbol: str, df: pd.DataFrame) -> bool:
        try:
            # Convert DataFrame to records
            records = df.to_dict("records")
            # Supabase upsert
            self.client.table("market_data").upsert(records).execute()
            return True
        except Exception as e:
            logging.error(f"Error saving market data to Supabase: {e}")
            return False

    def query_market_data(self, symbol: str, start: str, end: str) -> List[Dict]:
        try:
            response = self.client.table("market_data") \
                .select("*") \
                .eq("symbol", symbol) \
                .gte("timestamp", start) \
                .lte("timestamp", end) \
                .execute()

            return response.data
        except Exception as e:
            logging.error(f"Error querying market data from Supabase: {e}")
            return []
