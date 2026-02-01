
# tests/conftest.py
import os
import shutil
from datetime import datetime, timezone

import pytest
import yaml

from storage.sqlite_storage import SqliteStorage
from utils.crypto_utils import CryptoUtils
from utils.time_utils import TimeUtils


def load_all_config(config_dir="config"):
    """Loads all YAML configuration files for testing."""
    config = {}
    # Correctly resolve the config directory path relative to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_config_dir = os.path.join(project_root, config_dir)

    config_files = [
        os.path.join(full_config_dir, "system_config.yaml"),
        os.path.join(full_config_dir, "audit_rules.yaml"),
        os.path.join(full_config_dir, "regime_config.yaml"),
        os.path.join(full_config_dir, "parameter_bounds.yaml"),
        os.path.join(full_config_dir, "safe_baseline.yaml"),
    ]
    for file_path in config_files:
        with open(file_path, "r") as f:
            config_key = os.path.basename(file_path).replace(".yaml", "")
            config[config_key] = yaml.safe_load(f)
    return config


@pytest.fixture(scope="session")
def test_config():
    """Provides a consistent configuration loaded from YAML files for tests."""
    config = load_all_config()
    config["EXCHANGE_API_KEY"] = os.getenv("EXCHANGE_API_KEY", "test_api_key")
    config["EXCHANGE_SECRET_KEY"] = os.getenv("EXCHANGE_SECRET_KEY", "test_secret_key")
    config["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "test_deepseek_api_key")
    return config


import logging
import sqlite3


@pytest.fixture(scope="function")
def in_memory_state_manager(test_config, tmp_path):
    """Provides an in-memory SQLite Storage for isolated tests."""
    logging.info("Creating in-memory storage backend")

    db_path = ":memory:"
    artifacts_path = str(tmp_path / "test_artifacts")
    market_data_path = str(tmp_path / "test_market")

    storage = SqliteStorage(db_path, artifacts_path, market_data_path)

    # Initialize schema for tables used in legacy tests (if any still depend on direct SQL)
    # Use the connection from storage to ensure it's the same in-memory DB
    conn = storage._get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS parameter_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            params_hash TEXT NOT NULL,
            params_json TEXT NOT NULL,
            regime TEXT NOT NULL,
            profit_pct REAL,
            max_drawdown_pct REAL,
            win_rate REAL,
            total_trades INTEGER,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(params_hash, regime)
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_log (
            order_id TEXT PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            amount REAL,
            price REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            proposal_id TEXT
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS approval_tickets (
            ticket_id TEXT PRIMARY KEY,
            incident_id TEXT,
            description TEXT,
            requested_at DATETIME,
            approved_by TEXT,
            approved_at DATETIME,
            status TEXT, -- pending, approved, rejected, expired
            timeout_at DATETIME
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            params_hash TEXT NOT NULL UNIQUE,
            params_json TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS best_parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regime TEXT NOT NULL UNIQUE,
            params_json TEXT NOT NULL,
            profit_pct REAL,
            max_drawdown_pct REAL,
            iteration INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            type TEXT,
            details TEXT,
            proposal_id TEXT,
            timestamp DATETIME,
            status TEXT, -- active, resolved
            resolution TEXT,
            resolved_at DATETIME
        );
        """
    )
    conn.commit()
    # Note: We don't close the connection here because it's in-memory and held by storage

    return storage


@pytest.fixture(scope="function")
def temp_data_path(tmp_path):
    """Provides a temporary directory for data storage."""
    temp_dir = tmp_path / "test_data"
    temp_dir.mkdir()
    return temp_dir


@pytest.fixture(scope="session")
def time_utils():
    return TimeUtils()


@pytest.fixture(scope="session")
def crypto_utils():
    return CryptoUtils()
