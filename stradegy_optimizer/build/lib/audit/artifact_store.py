import logging
import json
from data_bus.schemas import AuditVerdict

class ArtifactStore:
    """
    Manages the immutable storage of audit artifacts, ensuring they are stored
    with a verifiable checksum.
    """
    def __init__(self, config, artifact_manager, crypto_utils):
        self.config = config
        self.artifact_manager = artifact_manager
        self.crypto_utils = crypto_utils
        logging.info("Initialized ArtifactStore.")

    def store_artifact(self, verdict: AuditVerdict) -> AuditVerdict:
        """
        Stores an audit verdict as a JSON artifact. The ArtifactManager handles checksum calculation.
        Returns the updated AuditVerdict with artifact_refs and checksum populated.
        """
        artifact_id = f"audit_{verdict.audit_id}.json"
        
        # The checksum is now calculated within the artifact_manager.
        verdict_json = verdict.model_dump_json(indent=4)
        
        uri, checksum = self.artifact_manager.upload_artifact(verdict_json, artifact_id)
        
        # Update the verdict object with the stored URI and checksum
        verdict.artifact_refs.append(uri)
        verdict.checksum = checksum
        
        logging.info(f"Stored audit artifact {artifact_id} at {uri} with checksum {checksum}")
        return verdict

    def retrieve_artifact(self, audit_id: str) -> AuditVerdict:
        """
        Retrieves and verifies an audit artifact using its checksum.
        """
        artifact_id = f"audit_{audit_id}.json"
        artifact_json, stored_checksum = self.artifact_manager.download_artifact(artifact_id)
        
        if not artifact_json:
            logging.error(f"Artifact {artifact_id} not found or is empty.")
            return None
        
        if not stored_checksum:
            logging.warning(f"Artifact {artifact_id} has no checksum. Cannot verify integrity.")
            # Depending on policy, you might reject it. For now, we proceed with caution.
            return AuditVerdict.model_validate_json(artifact_json)

        # Verify checksum
        calculated_checksum = self.crypto_utils.sha256_hash(artifact_json.encode('utf-8'))
        
        if calculated_checksum != stored_checksum:
            logging.error(f"Checksum mismatch for artifact {artifact_id}! "
                          f"Calculated: {calculated_checksum}, Stored: {stored_checksum}. Artifact is corrupt.")
            return None
            
        logging.info(f"Successfully retrieved and verified artifact {artifact_id}.")
        return AuditVerdict.model_validate_json(artifact_json)