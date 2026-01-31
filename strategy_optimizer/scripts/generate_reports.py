import sys
import os
import yaml
import json
from dotenv import load_dotenv
import logging
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.state_manager import StateManager
from src.storage.artifact_manager import ArtifactManager
from src.data_bus.schemas import AuditVerdict, BacktestResult # Assuming backtests could also be artifacts
from src.utils.logging_config import setup_logging
from src.utils.crypto_utils import CryptoUtils

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

def generate_reports(report_type: str, output_path: str = "reports"):
    """
    Generates reports by fetching real data from storage.
    """
    setup_logging()
    load_dotenv()
    logging.info(f"Generating {report_type} reports...")

    config = load_all_config()
    state_manager = StateManager(config)
    crypto_utils = CryptoUtils()
    artifact_manager = ArtifactManager(config, crypto_utils)

    os.makedirs(output_path, exist_ok=True)
    report_count = 0

    if report_type == "audit":
        logging.info("Generating all audit reports from local artifact storage.")
        artifacts_dir = Path(config['system_config']['paths']['artifacts'])
        audit_files = list(artifacts_dir.glob("audit_*.json"))
        
        for audit_file in audit_files:
            artifact_json, stored_checksum = artifact_manager.download_artifact(audit_file.name)
            if not artifact_json or not stored_checksum:
                logging.warning(f"Could not read or find checksum for {audit_file.name}, skipping.")
                continue

            # Verify checksum before including in report
            if crypto_utils.sha256_hash(artifact_json.encode('utf-8')) == stored_checksum:
                report_filename = os.path.join(output_path, f"report_{audit_file.name}")
                with open(report_filename, 'w') as f:
                    # Prettify the JSON for the report
                    data = json.loads(artifact_json)
                    json.dump(data, f, indent=4)
                logging.info(f"Generated audit report: {report_filename}")
                report_count += 1
            else:
                logging.error(f"Checksum mismatch for {audit_file.name}, flagging as corrupt.")

    elif report_type == "incidents":
        logging.info("Generating incident report from database.")
        incidents = state_manager.execute_query("SELECT * FROM incidents ORDER BY timestamp DESC", fetch='all')
        report_filename = os.path.join(output_path, f"incident_report_{datetime.now().strftime('%Y%m%d')}.json")
        
        incident_list = []
        for inc in incidents:
            incident_list.append({
                "incident_id": inc[0],
                "type": inc[1],
                "details": inc[2],
                "proposal_id": inc[3],
                "timestamp": inc[4],
                "status": inc[5],
                "resolution": inc[6],
                "resolved_at": inc[7],
            })
        with open(report_filename, 'w') as f:
            json.dump(incident_list, f, indent=4)
        report_count = len(incident_list)

    else:
        logging.warning(f"Unknown report type: {report_type}")

    logging.info(f"Report generation complete. Generated {report_count} report(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate various reports for the strategy optimizer.")
    parser.add_argument("--type", type=str, required=True, choices=["audit", "incidents"],
                        help="Type of report to generate.")
    parser.add_argument("--output", type=str, default="reports",
                        help="Output directory for generated reports.")
    
    import argparse
    args = parser.parse_args()
    
    generate_reports(args.type, args.output)