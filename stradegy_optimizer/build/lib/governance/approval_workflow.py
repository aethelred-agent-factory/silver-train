import logging
import uuid
from datetime import datetime, timedelta

class ApprovalWorkflow:
    """
    Manages a human-in-the-loop approval system for critical actions.
    """
    def __init__(self, config, state_manager):
        self.config = config
        self.state_manager = state_manager
        # Ensure approval tickets table exists
        self.state_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS approval_tickets (
                ticket_id TEXT PRIMARY KEY,
                incident_id TEXT,
                description TEXT,
                requested_at DATETIME,
                approved_by TEXT,
                approved_at DATETIME,
                status TEXT, -- pending, approved, rejected, expired
                timeout_at DATETIME
            );
        """)
        logging.info("Initialized ApprovalWorkflow.")

    def request_approval(self, incident_id: str, description: str, timeout_hours: int = 4) -> str:
        """
        Creates an approval ticket and requests human approval.
        """
        ticket_id = str(uuid.uuid4())
        requested_at = datetime.utcnow()
        timeout_at = requested_at + timedelta(hours=timeout_hours)
        
        self.state_manager.execute_query(
            "INSERT INTO approval_tickets (ticket_id, incident_id, description, requested_at, status, timeout_at) VALUES (?, ?, ?, ?, ?, ?)",
            (ticket_id, incident_id, description, requested_at.isoformat(), 'pending', timeout_at.isoformat())
        )
        logging.warning(f"Approval requested for incident {incident_id}. Ticket ID: {ticket_id}")
        return ticket_id

    def approve_ticket(self, ticket_id: str, approver: str) -> bool:
        """
        Approves a pending ticket.
        """
        current_status = self._get_ticket_status(ticket_id)
        if current_status == 'pending':
            self.state_manager.execute_query(
                "UPDATE approval_tickets SET status = ?, approved_by = ?, approved_at = ? WHERE ticket_id = ?",
                ('approved', approver, datetime.utcnow().isoformat(), ticket_id)
            )
            logging.info(f"Approval ticket {ticket_id} approved by {approver}.")
            return True
        logging.warning(f"Cannot approve ticket {ticket_id}. Current status: {current_status}")
        return False

    def reject_ticket(self, ticket_id: str, approver: str) -> bool:
        """
        Rejects a pending ticket.
        """
        current_status = self._get_ticket_status(ticket_id)
        if current_status == 'pending':
            self.state_manager.execute_query(
                "UPDATE approval_tickets SET status = ?, approved_by = ?, approved_at = ? WHERE ticket_id = ?",
                ('rejected', approver, datetime.utcnow().isoformat(), ticket_id)
            )
            logging.warning(f"Approval ticket {ticket_id} rejected by {approver}.")
            return True
        logging.warning(f"Cannot reject ticket {ticket_id}. Current status: {current_status}")
        return False

    def check_approval_status(self, ticket_id: str) -> str:
        """
        Checks the current status of an approval ticket.
        Returns 'pending', 'approved', 'rejected', or 'expired'.
        """
        query = "SELECT status, timeout_at FROM approval_tickets WHERE ticket_id = ?"
        result = self.state_manager.execute_query(query, (ticket_id,), fetch='one')
        if result:
            status, timeout_at_str = result
            if status == 'pending' and datetime.utcnow() > datetime.fromisoformat(timeout_at_str):
                self.state_manager.execute_query(
                    "UPDATE approval_tickets SET status = ? WHERE ticket_id = ?",
                    ('expired', ticket_id)
                )
                return 'expired'
            return status
        return None

    def _get_ticket_status(self, ticket_id: str) -> str:
        query = "SELECT status FROM approval_tickets WHERE ticket_id = ?"
        result = self.state_manager.execute_query(query, (ticket_id,), fetch='one')
        return result[0] if result else None
