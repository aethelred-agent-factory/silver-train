import sys
import os
import yaml
import json
from dotenv import load_dotenv
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_bus.schemas import OptimizerProposal
from src.data_bus.event_bus import EventBus
from src.audit.audit_layer import AuditLayer
from src.audit.t1_checks import T1Checks
from src.audit.t2_checks import T2Checks
from src.audit.t3_checks import T3Checks
from src.audit.causal_chain_validator import CausalChainValidator as AuditCausalChainValidator
from src.audit.artifact_store import ArtifactStore
from src.storage.artifact_manager import ArtifactManager
from src.storage.state_manager import StateManager
from src.utils.crypto_utils import CryptoUtils
from src.utils.logging_config import setup_logging
from datetime import datetime, timezone

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

def run_audit_only(proposal_json_path: str = None):
    """
    Runs the audit layer on a proposal loaded from a JSON file.
    """
    setup_logging()
    load_dotenv()
    logging.info("Starting audit-only run...")

    config = load_all_config()
    state_manager = StateManager(config)
    crypto_utils = CryptoUtils()
    artifact_manager = ArtifactManager(config, crypto_utils)
    
    # Initialize audit components
    t1_checks = T1Checks(config)
    t2_checks = T2Checks(config)
    t3_checks = T3Checks(config)
    audit_causal_validator = AuditCausalChainValidator(config, artifact_manager)
    artifact_store = ArtifactStore(config, artifact_manager, crypto_utils)
    event_bus = EventBus(state_manager)

    audit_layer = AuditLayer(config, event_bus, t1_checks, t2_checks, t3_checks, audit_causal_validator, artifact_store)

    proposal_to_audit = None
    if proposal_json_path:
        try:
            with open(proposal_json_path, 'r') as f:
                proposal_json = f.read()
            proposal_to_audit = OptimizerProposal.model_validate_json(proposal_json)
            logging.info(f"Auditing proposal from file: {proposal_json_path}")
        except FileNotFoundError:
            logging.error(f"File not found: {proposal_json_path}")
            return
        except Exception as e:
            logging.error(f"Invalid proposal JSON in file '{proposal_json_path}': {e}")
            return
    else:
        logging.error("No proposal JSON file path provided for audit.")
        return

    if proposal_to_audit:
        verdict = audit_layer.audit_proposal(proposal_to_audit)
        logging.info(f"--- AUDIT COMPLETE for proposal {proposal_to_audit.proposal_id} ---")
        logging.info(f"Final Verdict: {verdict.action.type}")
        if verdict.action.restrictions:
            logging.info(f"Restrictions: {verdict.action.restrictions}")
        
        logging.info("Findings:")
        if not verdict.tiered_findings:
            logging.info("  No findings.")
        for finding in verdict.tiered_findings:
            logging.info(f"  - {finding.tier} | {finding.code}: {finding.explanation}")
        logging.info("--- END OF AUDIT ---")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the audit layer on a specific proposal from a JSON file.")
    parser.add_argument("--proposal_file", type=str, required=True, help="Path to the JSON file containing the proposal to audit.")
    
    args = parser.parse_args()
    
    run_audit_only(proposal_json_path=args.proposal_file)