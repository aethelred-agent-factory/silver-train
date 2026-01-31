import os
import sys

import yaml

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.storage.state_manager import StateManager
from src.utils.logging_config import setup_logging


def load_config(config_path="config/system_config.yaml"):
    """Loads a single YAML configuration file."""
    # Construct absolute path to config file
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    absolute_path = os.path.join(base_dir, config_path)

    with open(absolute_path, "r") as f:
        return yaml.safe_load(f)


def initialize_db():
    """
    Initializes the SQLite database schema by creating all necessary tables
    for each component.
    """
    setup_logging()
    print("Initializing database...")

    # Load only necessary part of config for StateManager
    system_config_raw = load_config()
    config = {"system_config": system_config_raw}

    state_manager = StateManager(config)

    print("Creating tables for all components...")

    # EventBus tables
    state_manager.execute_query(
        """
        CREATE TABLE IF NOT EXISTS event_bus_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, done
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    )
    state_manager.execute_query(
        """
        CREATE TABLE IF NOT EXISTS event_bus_verdicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verdict_id TEXT NOT NULL UNIQUE,
            proposal_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # ParameterMemory table
    state_manager.execute_query(
        """
        CREATE TABLE IF NOT EXISTS parameter_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            params_hash TEXT NOT NULL,
            regime TEXT NOT NULL,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # OrderManager table
    state_manager.execute_query(
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

    # ApprovalWorkflow table
    state_manager.execute_query(
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

    # IncidentTracker table
    state_manager.execute_query(
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

    print("Database initialization complete.")


if __name__ == "__main__":
    initialize_db()
