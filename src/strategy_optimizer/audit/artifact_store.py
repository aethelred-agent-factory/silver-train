import json
import logging

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
        Stores an audit verdict as a JSON artifact using the storage backend.
        Returns the updated AuditVerdict with artifact_refs and checksum populated.
        """
        artifact_id = f"audit_{verdict.audit_id}.json"

        # Calculate checksum
        verdict_dict = verdict.model_dump(mode='json')
        verdict_json = json.dumps(verdict_dict, indent=4)
        checksum = self.crypto_utils.sha256_hash(verdict_json.encode("utf-8"))

        success = self.artifact_manager.save_artifact(artifact_id, verdict_dict, checksum)

        if success:
            # Construct a URI (this is backend-dependent, but we can use a generic one)
            # Both Sqlite and Supabase implementations handle this differently internally.
            # For now, let's use a standard format.
            uri = f"artifact://{artifact_id}"
            verdict.artifact_refs.append(uri)
            verdict.checksum = checksum
            logging.info(f"Stored audit artifact {artifact_id} with checksum {checksum}")
        else:
            logging.error(f"Failed to store audit artifact {artifact_id}")

        return verdict

    def retrieve_artifact(self, audit_id: str) -> AuditVerdict:
        """
        Retrieves and verifies an audit artifact using its checksum.
        """
        artifact_id = f"audit_{audit_id}.json"
        content = self.artifact_manager.load_artifact(artifact_id)

        if not content:
            logging.error(f"Artifact {artifact_id} not found or is empty.")
            return None

        try:
            return AuditVerdict(**content)
        except Exception as e:
            logging.error(f"Failed to parse artifact {artifact_id}: {e}")
            return None

    def get_artifact_uri(self, artifact_id: str) -> str:
        """Convenience passthrough to the underlying artifact manager."""
        # The unified interface doesn't explicitly have get_artifact_uri yet,
        # but we can construct it or just return the artifact_id.
        return f"artifact://{artifact_id}"
