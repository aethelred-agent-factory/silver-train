import logging
import uuid
from datetime import datetime, timedelta

from storage.interface import StorageInterface

APPROVAL_TICKETS_KEY = "approval_tickets"

class ApprovalWorkflow:
    """
    Manages a human-in-the-loop approval system for critical actions.
    """

    def __init__(self, config, storage: StorageInterface):
        self.config = config
        self.storage = storage
        logging.info("Initialized ApprovalWorkflow.")

    def _load_tickets(self) -> list:
        tickets = self.storage.load_state(APPROVAL_TICKETS_KEY)
        return tickets if tickets is not None else []

    def _save_tickets(self, tickets: list):
        self.storage.save_state(APPROVAL_TICKETS_KEY, tickets)

    def request_approval(
        self, incident_id: str, description: str, timeout_hours: int = 4
    ) -> str:
        """
        Creates an approval ticket and requests human approval.
        """
        ticket_id = str(uuid.uuid4())
        requested_at = datetime.utcnow()
        timeout_at = requested_at + timedelta(hours=timeout_hours)

        tickets = self._load_tickets()
        tickets.append({
            "ticket_id": ticket_id,
            "incident_id": incident_id,
            "description": description,
            "requested_at": requested_at.isoformat(),
            "approved_by": None,
            "approved_at": None,
            "status": "pending", # pending, approved, rejected, expired
            "timeout_at": timeout_at.isoformat(),
        })
        self._save_tickets(tickets)

        logging.warning(
            f"Approval requested for incident {incident_id}. Ticket ID: {ticket_id}"
        )
        return ticket_id

    def approve_ticket(self, ticket_id: str, approver: str) -> bool:
        """
        Approves a pending ticket.
        """
        tickets = self._load_tickets()
        ticket_found = False
        for ticket in tickets:
            if ticket["ticket_id"] == ticket_id and ticket["status"] == "pending":
                ticket["status"] = "approved"
                ticket["approved_by"] = approver
                ticket["approved_at"] = datetime.utcnow().isoformat()
                ticket_found = True
                break
        
        if ticket_found:
            self._save_tickets(tickets)
            logging.info(f"Approval ticket {ticket_id} approved by {approver}.")
            return True
        
        logging.warning(
            f"Cannot approve ticket {ticket_id}. It might not exist or is not in 'pending' status."
        )
        return False

    def reject_ticket(self, ticket_id: str, approver: str) -> bool:
        """
        Rejects a pending ticket.
        """
        tickets = self._load_tickets()
        ticket_found = False
        for ticket in tickets:
            if ticket["ticket_id"] == ticket_id and ticket["status"] == "pending":
                ticket["status"] = "rejected"
                ticket["approved_by"] = approver # approver is the one rejecting
                ticket["approved_at"] = datetime.utcnow().isoformat()
                ticket_found = True
                break

        if ticket_found:
            self._save_tickets(tickets)
            logging.warning(f"Approval ticket {ticket_id} rejected by {approver}.")
            return True

        logging.warning(
            f"Cannot reject ticket {ticket_id}. It might not exist or is not in 'pending' status."
        )
        return False

    def check_approval_status(self, ticket_id: str) -> str:
        """
        Checks the current status of an approval ticket.
        Returns 'pending', 'approved', 'rejected', or 'expired'.
        """
        tickets = self._load_tickets()
        for ticket in tickets:
            if ticket["ticket_id"] == ticket_id:
                if ticket["status"] == "pending" and datetime.utcnow() > datetime.fromisoformat(ticket["timeout_at"]):
                    ticket["status"] = "expired"
                    self._save_tickets(tickets)
                    return "expired"
                return ticket["status"]
        return None
