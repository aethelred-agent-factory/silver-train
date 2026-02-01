import os
from .interface import StorageInterface
from .sqlite_storage import SqliteStorage

def get_storage_backend() -> StorageInterface:
    backend = os.getenv("DATABASE_BACKEND", "sqlite")
    
    if backend == "sqlite":
        db_path = os.getenv("SQLITE_PATH", "data/state/optimizer_state.db")
        artifacts_path = os.getenv("ARTIFACTS_PATH", "data/artifacts")
        market_data_path = os.getenv("MARKET_DATA_PATH", "data/market")
        return SqliteStorage(db_path, artifacts_path, market_data_path)
    
    raise ValueError(f"Unknown backend: {backend}")
