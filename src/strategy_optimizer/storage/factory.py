import os
from .interface import StorageInterface
from .sqlite_storage import SqliteStorage
from .supabase_storage import SupabaseStorage

def get_storage_backend() -> StorageInterface:
    backend = os.getenv("DATABASE_BACKEND", "sqlite")
    
    if backend == "sqlite":
        db_path = os.getenv("SQLITE_PATH", "data/state/optimizer_state.db")
        artifacts_path = os.getenv("ARTIFACTS_PATH", "data/artifacts")
        market_data_path = os.getenv("MARKET_DATA_PATH", "data/market")
        return SqliteStorage(db_path, artifacts_path, market_data_path)
    
    elif backend == "supabase":
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        bucket = os.getenv("SUPABASE_ARTIFACTS_BUCKET", "artifacts")

        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set for supabase backend")

        return SupabaseStorage(url, key, bucket)

    raise ValueError(f"Unknown backend: {backend}")
