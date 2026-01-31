import logging
import uuid
from datetime import datetime


class IncidentTracker:
    """
    Tracks T1 incidents and their resolutions in the state database.
    """

    def __init__(self, config, state_manager):
        self.config = config
        self.state_manager = state_manager
        # Ensure incident log table exists
        self.state_manager.execute_query(
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
        logging.info("Initialized IncidentTracker.")

    def log_incident(self, type: str, details: str, proposal_id: str = None) -> str:
        """
        Logs a new incident to the database.
        """
        incident_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        self.state_manager.execute_query(
            "INSERT INTO incidents (incident_id, type, details, proposal_id, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)",
            (incident_id, type, details, proposal_id, timestamp, "active"),
        )
        logging.critical(f"Incident logged: {type} - {details} (ID: {incident_id})")
        return incident_id

    def mark_resolved(self, incident_id: str, resolution: str):
        """
        Marks an active incident as resolved with a resolution message.
        """
        resolved_at = datetime.utcnow().isoformat()
        self.state_manager.execute_query(
            "UPDATE incidents SET status = ?, resolution = ?, resolved_at = ? WHERE incident_id = ?",
            ("resolved", resolution, resolved_at, incident_id),
        )
        logging.info(f"Incident {incident_id} marked as resolved.")

    def get_active_incidents(self) -> list:
        """
        Retrieves all currently active incidents.
        """
        query = "SELECT * FROM incidents WHERE status = 'active'"
        return self.state_manager.execute_query(query, fetch="all")

    def get_incident_history(self, incident_id: str = None) -> list:
        """
        Retrieves incident history, optionally for a specific incident.
        """
        if incident_id:
            query = "SELECT * FROM incidents WHERE incident_id = ?"
            return self.state_manager.execute_query(query, (incident_id,), fetch="all")
        else:
            query = "SELECT * FROM incidents"
            return self.state_manager.execute_query(query, fetch="all")
