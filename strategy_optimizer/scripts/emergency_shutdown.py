import sys
import os
import yaml
from dotenv import load_dotenv
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.governance.emergency_manager import EmergencyManager
from src.governance.incident_tracker import IncidentTracker
from src.governance.approval_workflow import ApprovalWorkflow
from src.storage.state_manager import StateManager
from src.utils.logging_config import setup_logging

def load_all_config(config_dir='config'):
    """Loads all YAML configuration files."""
    config = {}
    config_files = [
        os.path.join(config_dir, 'system_config.yaml'),
        os.path.join(config_dir, 'audit_rules.yaml'),
        os.path.join(config_dir, 'regime_config.yaml'),
        os.path.join(config_dir, 'parameter_bounds.yaml'),
        os.path.join(config_dir, 'safe_baseline.yaml')
    ]
    for file_path in config_files:
        with open(file_path, 'r') as f:
            config_key = os.path.basename(file_path).replace('.yaml', '')
            config[config_key] = yaml.safe_load(f)
    return config

def emergency_shutdown(reason: str):
    """
    Triggers an emergency shutdown of the system.
    """
    setup_logging()
    load_dotenv()
    logging.critical(f"MANUAL EMERGENCY SHUTDOWN INITIATED. Reason: {reason}")

    config = load_all_config()
    state_manager = StateManager(config)
    
    incident_tracker = IncidentTracker(config, state_manager)
    approval_workflow = ApprovalWorkflow(config, state_manager)
    
    emergency_manager = EmergencyManager(config, incident_tracker, approval_workflow)
    
    emergency_manager.trigger_emergency(
        incident_type="MANUAL_SHUTDOWN",
        details=f"Manual intervention: {reason}"
    )

    logging.critical("Emergency shutdown script finished.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Initiate an emergency shutdown of the strategy optimizer.")
    parser.add_argument("--reason", type=str, required=True, help="Reason for the emergency shutdown.")
    
    args = parser.parse_args()
    
    emergency_shutdown(args.reason)
