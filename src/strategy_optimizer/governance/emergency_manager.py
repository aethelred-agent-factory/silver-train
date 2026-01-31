import logging


class EmergencyManager:
    """
    Executes emergency protocols, triggered by critical incidents (e.g., T1 audit failures).
    """

    def __init__(self, config, incident_tracker, approval_workflow):
        self.config = config
        self.incident_tracker = incident_tracker
        self.approval_workflow = approval_workflow
        self.system_halted = False
        self.safe_baseline_params = config["safe_baseline"]
        logging.info("Initialized EmergencyManager.")

    def trigger_emergency(
        self, incident_type: str, details: str, proposal_id: str = None
    ):
        """
        Triggers an emergency protocol: halts the system, logs an incident, and alerts.
        """
        if self.system_halted:
            logging.warning(
                "System already halted. Skipping duplicate emergency trigger."
            )
            return

        logging.critical(f"EMERGENCY TRIGGERED: {incident_type} - {details}")
        self.system_halted = True

        # 1. Log the incident
        incident_id = self.incident_tracker.log_incident(
            type=incident_type, details=details, proposal_id=proposal_id
        )
        logging.info(f"Incident {incident_id} logged.")

        # 2. Revert to safe baseline (if applicable)
        self.revert_to_safe_baseline()

        # 3. Request human approval (for resolution)
        # Placeholder for actual approval workflow integration
        logging.debug("Approval workflow initiation (placeholder).")

        # 4. Alerting (to be implemented in monitoring)
        # Placeholder for actual alerting integration
        logging.debug("Alerting (placeholder).")

        logging.info("Emergency protocol executed. System is halted.")

    def revert_to_safe_baseline(self):
        """
        Reverts the active trading parameters to a predefined safe baseline.
        """
        logging.warning("Reverting to safe baseline parameters...")
        # In a real system, this would update the active parameters
        # that the execution engine uses.
        # For now, it just logs the action.
        logging.info(f"Safe baseline parameters: {self.safe_baseline_params}")

    def is_system_halted(self) -> bool:
        """
        Checks if the system is currently halted.
        """
        return self.system_halted

    def resume_system(self, incident_id: str, resolution: str):
        """
        Resumes system operation after an emergency, typically after human approval.
        """
        # Placeholder for actual approval workflow check
        logging.debug("Approval workflow check (placeholder).")

        logging.info(
            f"System resume initiated for incident {incident_id}. Resolution: {resolution}"
        )
        self.system_halted = False
        self.incident_tracker.mark_resolved(incident_id, resolution)
        logging.info("System resumed successfully.")
