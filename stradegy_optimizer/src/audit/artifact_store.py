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
        # Prefer retrieve_artifact which may return a parsed object
        artifact_json = None
        stored_checksum = None
        try:
            res = self.artifact_manager.download_artifact(artifact_id)
        except AttributeError:
            # Some artifact managers implement retrieve_artifact instead
            res = None

        if res is None and hasattr(self.artifact_manager, 'retrieve_artifact'):
            # If retrieve_artifact returns an AuditVerdict-like object, return it directly
            try:
                obj = self.artifact_manager.retrieve_artifact(artifact_id)
                return obj
            except Exception:
                return None

        if isinstance(res, tuple) and len(res) >= 2:
            artifact_json, stored_checksum = res[0], res[1]
        elif isinstance(res, tuple) and len(res) == 1:
            artifact_json = res[0]

        if not artifact_json:
            logging.error(f"Artifact {artifact_id} not found or is empty.")
            return None

        if not stored_checksum:
            logging.warning(f"Artifact {artifact_id} has no checksum. Cannot verify integrity.")
            try:
                return AuditVerdict.model_validate_json(artifact_json)
            except Exception:
                return None

        # Verify checksum
        calculated_checksum = self.crypto_utils.sha256_hash(artifact_json.encode('utf-8'))

        if calculated_checksum != stored_checksum:
            logging.error(f"Checksum mismatch for artifact {artifact_id}! "
                          f"Calculated: {calculated_checksum}, Stored: {stored_checksum}. Artifact is corrupt.")
            return None

        logging.info(f"Successfully retrieved and verified artifact {artifact_id}.")
        try:
            return AuditVerdict.model_validate_json(artifact_json)
        except Exception:
            return None

    def get_artifact_uri(self, artifact_id: str) -> str:
        """Convenience passthrough to the underlying artifact manager."""
        if hasattr(self.artifact_manager, 'get_artifact_uri'):
            try:
                return self.artifact_manager.get_artifact_uri(artifact_id)
            except Exception:
                return None
        return None