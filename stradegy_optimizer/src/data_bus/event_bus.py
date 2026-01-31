import logging
from typing import Optional
from data_bus.schemas import OptimizerProposal, AuditVerdict
from storage.state_manager import StateManager
from datetime import datetime

class EventBus:
    """
    A persistent event bus backed by the StateManager (SQLite) for robust communication
    between the optimizer and the audit layer.
    """
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        # Ensure tables exist
        self._initialize_schema()
        logging.info("Initialized persistent EventBus.")

    def _initialize_schema(self):
        """Creates the necessary tables for the event bus."""
        self.state_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS event_bus_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, done
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.state_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS event_bus_verdicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verdict_id TEXT NOT NULL UNIQUE,
                proposal_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def publish_proposal(self, proposal: OptimizerProposal):
        """Publishes an optimizer proposal to the persistent queue."""
        payload = proposal.model_dump_json()
        query = "INSERT INTO event_bus_proposals (proposal_id, payload) VALUES (?, ?)"
        self.state_manager.execute_query(query, (proposal.proposal_id, payload))
        logging.info(f"Published proposal {proposal.proposal_id} to the persistent event bus.")

    def subscribe_proposal(self) -> Optional[OptimizerProposal]:
        """
        Subscribes to an optimizer proposal, marking it as 'processing' to prevent re-delivery.
        """
        query_select = "SELECT id, payload FROM event_bus_proposals WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
        result = self.state_manager.execute_query(query_select, fetch='one')

        if not result:
            return None
            
        event_id, payload = result
        query_update = "UPDATE event_bus_proposals SET status = 'processing' WHERE id = ?"
        self.state_manager.execute_query(query_update, (event_id,))
        
        proposal = OptimizerProposal.model_validate_json(payload)
        logging.info(f"Subscribed to proposal {proposal.proposal_id} from the persistent event bus.")
        return proposal

    def acknowledge_proposal(self, proposal_id: str):
        """Marks a proposal as 'done' after it has been fully processed (audited)."""
        query = "UPDATE event_bus_proposals SET status = 'done' WHERE proposal_id = ?"
        self.state_manager.execute_query(query, (proposal_id,))
        logging.debug(f"Acknowledged proposal {proposal_id}.")

    def publish_verdict(self, verdict: AuditVerdict):
        """Publishes an audit verdict to the persistent queue."""
        payload = verdict.model_dump_json()
        query = "INSERT INTO event_bus_verdicts (verdict_id, proposal_id, payload) VALUES (?, ?, ?)"
        self.state_manager.execute_query(query, (verdict.audit_id, verdict.proposal_id, payload))
        logging.info(f"Published verdict {verdict.audit_id} for proposal {verdict.proposal_id}.")

    def subscribe_verdict(self, proposal_id: Optional[str] = None) -> Optional[AuditVerdict]:
        """
        Subscribes to an audit verdict. If `proposal_id` is provided, returns verdict for that proposal,
        otherwise returns the next pending verdict available.
        """
        if proposal_id:
            query = "SELECT payload FROM event_bus_verdicts WHERE proposal_id = ? AND status = 'pending' LIMIT 1"
            result = self.state_manager.execute_query(query, (proposal_id,), fetch='one')
        else:
            query = "SELECT payload FROM event_bus_verdicts WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
            result = self.state_manager.execute_query(query, fetch='one')
        
        if not result:
            return None
        
        payload = result[0]
        verdict = AuditVerdict.model_validate_json(payload)
        
        # Mark as done
        query_update = "UPDATE event_bus_verdicts SET status = 'done' WHERE verdict_id = ?"
        self.state_manager.execute_query(query_update, (verdict.audit_id,))
        
        logging.info(f"Subscribed to verdict {verdict.audit_id} for proposal {proposal_id}.")
        return verdict