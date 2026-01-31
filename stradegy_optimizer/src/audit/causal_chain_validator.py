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
        logging.info(f"Validating causal chain for proposal {getattr(proposal, 'proposal_id', '<unknown>')}")

        if not proposal.causal_chain_refs:
            logging.warning(f"Proposal {proposal.proposal_id} has an empty causal chain. Cannot validate.")
            # This is not a failure, but a state to be noted (and potentially flagged as T2).
            return True

        for ref in proposal.causal_chain_refs:
            # Artifact IDs are expected to be retrievable via the manager
            artifact_id = ref.id
            # Prefer a higher-level retrieve_artifact API that returns an object (or None)
            artifact_obj = None
            try:
                # Some managers expose retrieve_artifact for metadata inspection
                artifact_obj = self.artifact_manager.retrieve_artifact(artifact_id)
            except AttributeError:
                # Fallback to download_artifact which may return JSON
                try:
                    result = self.artifact_manager.download_artifact(artifact_id)
                except Exception:
                    result = None

                if isinstance(result, tuple) and len(result) >= 1:
                    artifact_json = result[0]
                    if artifact_json:
                        try:
                            data = json.loads(artifact_json)
                            ts = data.get('timestamp')
                            if ts:
                                artifact_obj = type('obj', (object,), {'timestamp': datetime.fromisoformat(ts)})()
                        except Exception:
                            artifact_obj = None

            if not artifact_obj:
                logging.error(f"Causal chain validation failed: Artifact {artifact_id} not found.")
                return False

            # artifact_obj is expected to have a 'timestamp' attribute
            try:
                artifact_timestamp = getattr(artifact_obj, 'timestamp')
                if artifact_timestamp >= proposal.timestamp:
                    logging.error(
                        f"Causal chain validation failed: Artifact {artifact_id} "
                        f"({artifact_timestamp}) is not strictly older than proposal ({proposal.timestamp})."
                    )
                    return False
            except Exception as e:
                logging.error(f"Causal chain validation failed: Could not read timestamp from artifact {artifact_id}. Error: {e}")
                return False

        logging.info(f"Causal chain for proposal {proposal.proposal_id} is valid.")
        return True