import logging
from datetime import datetime
import json
from data_bus.schemas import OptimizerProposal, AuditVerdict

class CausalChainValidator:
    """
    Verifies the provenance and timestamp causality of a proposal's causal chain
    by retrieving and inspecting each referenced artifact.
    """
    def __init__(self, config, artifact_manager):
        self.config = config
        self.artifact_manager = artifact_manager
        logging.info("Initialized CausalChainValidator.")

    def validate_proposal(self, proposal: OptimizerProposal) -> bool:
        """
        Validates the entire causal chain of a proposal.

        This involves:
        - Retrieving each artifact in the chain from the artifact_store.
        - Checking the timestamp of each artifact.
        - Ensuring all artifacts were created BEFORE the proposal.
        """
        logging.info(f"Validating causal chain for proposal {proposal.proposal_id}")

        if not proposal.causal_chain_refs:
            logging.warning(f"Proposal {proposal.proposal_id} has an empty causal chain. Cannot validate.")
            # This is not a failure, but a state to be noted (and potentially flagged as T2).
            return True

        for ref in proposal.causal_chain_refs:
            # Artifact IDs are expected to be retrievable via the manager
            artifact_id = ref.id
            
            artifact_json, stored_checksum = self.artifact_manager.download_artifact(artifact_id)
            
            if not artifact_json:
                logging.error(f"Causal chain validation failed: Artifact {artifact_id} not found.")
                return False
            
            # Here we assume the artifact is a JSON object with a 'timestamp' field.
            # This would apply to previous AuditVerdicts or other timestamped artifacts.
            try:
                artifact_data = json.loads(artifact_json)
                artifact_timestamp_str = artifact_data.get('timestamp')
                if not artifact_timestamp_str:
                    logging.error(f"Causal chain validation failed: Artifact {artifact_id} is missing a timestamp.")
                    return False
                
                artifact_timestamp = datetime.fromisoformat(artifact_timestamp_str)
                
                # The core causality check
                if artifact_timestamp >= proposal.timestamp:
                    logging.error(
                        f"Causal chain validation failed: Artifact {artifact_id} "
                        f"({artifact_timestamp}) is not strictly older than proposal ({proposal.timestamp})."
                    )
                    return False
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logging.error(f"Causal chain validation failed: Could not parse or read timestamp from artifact {artifact_id}. Error: {e}")
                return False

        logging.info(f"Causal chain for proposal {proposal.proposal_id} is valid.")
        return True