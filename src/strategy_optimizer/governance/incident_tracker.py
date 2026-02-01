import logging
import uuid
from datetime import datetime

from storage.interface import StorageInterface

INCIDENTS_KEY = "incidents"

class IncidentTracker:
    """
    Tracks T1 incidents and their resolutions in the state database.
    """

    def __init__(self, config, storage: StorageInterface):
        self.config = config
        self.storage = storage
        logging.info("Initialized IncidentTracker.")

    def _load_incidents(self) -> list:
        incidents = self.storage.load_state(INCIDENTS_KEY)
        return incidents if incidents is not None else []

    def _save_incidents(self, incidents: list):
        self.storage.save_state(INCIDENTS_KEY, incidents)

    def log_incident(self, type: str, details: str, proposal_id: str = None) -> str:
        """
        Logs a new incident to the database.
        """
        incident_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        incidents = self._load_incidents()
        incidents.append({
            "incident_id": incident_id,
            "type": type,
            "details": details,
            "proposal_id": proposal_id,
            "timestamp": timestamp,
            "status": "active",
            "resolution": None,
            "resolved_at": None,
        })
        self._save_incidents(incidents)

        logging.critical(f"Incident logged: {type} - {details} (ID: {incident_id})")
        return incident_id

    def mark_resolved(self, incident_id: str, resolution: str):
        """
        Marks an active incident as resolved with a resolution message.
        """
        resolved_at = datetime.utcnow().isoformat()
        incidents = self._load_incidents()
        for incident in incidents:
            if incident["incident_id"] == incident_id:
                incident["status"] = "resolved"
                incident["resolution"] = resolution
                incident["resolved_at"] = resolved_at
                break
        self._save_incidents(incidents)
        logging.info(f"Incident {incident_id} marked as resolved.")

    def get_active_incidents(self) -> list:
        """
        Retrieves all currently active incidents.
        """
        incidents = self._load_incidents()
        return [incident for incident in incidents if incident["status"] == "active"]

    def get_incident_history(self, incident_id: str = None) -> list:
        """
        Retrieves incident history, optionally for a specific incident.
        """
        incidents = self._load_incidents()
        if incident_id:
            return [incident for incident in incidents if incident["incident_id"] == incident_id]
        else:
            return incidents
