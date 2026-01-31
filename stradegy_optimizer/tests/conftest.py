# tests/conftest.py
import pytest
import os
import shutil
import yaml
from datetime import datetime, timezone

# Add parent directory and src directory to path to allow importing modules correctly
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.utils.time_utils import TimeUtils
from src.utils.crypto_utils import CryptoUtils
from src.storage.state_manager import StateManager

def load_all_config(config_dir='config'):
    """Loads all YAML configuration files for testing."""
    config = {}
    # Correctly resolve the config directory path relative to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    full_config_dir = os.path.join(project_root, config_dir)
    
    config_files = [
        os.path.join(full_config_dir, 'system_config.yaml'),
        os.path.join(full_config_dir, 'audit_rules.yaml'),
        os.path.join(full_config_dir, 'regime_config.yaml'),
        os.path.join(full_config_dir, 'parameter_bounds.yaml'),
        os.path.join(full_config_dir, 'safe_baseline.yaml')
    ]
    for file_path in config_files:
        with open(file_path, 'r') as f:
            config_key = os.path.basename(file_path).replace('.yaml', '')
            config[config_key] = yaml.safe_load(f)
    return config

@pytest.fixture(scope="session")
def test_config():
    """Provides a consistent configuration loaded from YAML files for tests."""
    config = load_all_config()
    config['EXCHANGE_API_KEY'] = os.getenv('EXCHANGE_API_KEY', 'test_api_key')
    config['EXCHANGE_SECRET_KEY'] = os.getenv('EXCHANGE_SECRET_KEY', 'test_secret_key')
    config['DEEPSEEK_API_KEY'] = os.getenv('DEEPSEEK_API_KEY', 'test_deepseek_api_key')
    return config

import logging

@pytest.fixture(scope="function")
def in_memory_state_manager(test_config):
    """Provides an in-memory SQLite StateManager for isolated tests."""
    logging.info("Creating in-memory state manager")
    # Create a copy of the config to avoid modifying the session-scoped fixture
    config_copy = test_config.copy()
    config_copy['system_config']['paths']['state_db'] = ':memory:'
    sm = StateManager(config_copy)
    # Initialize schema for the in-memory database
    sm.execute_query("""
        CREATE TABLE IF NOT EXISTS event_bus_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, done
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    sm.execute_query("""
        CREATE TABLE IF NOT EXISTS event_bus_verdicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verdict_id TEXT NOT NULL UNIQUE,
            proposal_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    sm.execute_query("""
        CREATE TABLE IF NOT EXISTS parameter_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            params_hash TEXT NOT NULL,
            regime TEXT NOT NULL,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    sm.execute_query("""
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
    """)
    sm.execute_query("""
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
    """)
    sm.execute_query("""
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
    """)
    return sm

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