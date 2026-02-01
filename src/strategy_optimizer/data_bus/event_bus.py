import logging
import time
import json
from typing import Optional, List

from data_bus.schemas import AuditVerdict, OptimizerProposal
from storage.interface import StorageInterface

PROPOSALS_PENDING_KEY = "event_bus:proposals:pending"
PROPOSALS_PROCESSING_KEY = "event_bus:proposals:processing"
VERDICTS_KEY_PREFIX = "event_bus:verdict:"
LATEST_VERDICT_ID_KEY = "event_bus:latest_verdict_id"
EVENTS_KEY_PREFIX = "event_bus:event:"

class EventBus:
    """
    A persistent event bus backed by the StorageInterface for robust communication
    between the optimizer and the audit layer.
    """

    def __init__(self, storage: StorageInterface):
        self.storage = storage
        logging.info("Initialized persistent EventBus.")

    def publish_proposal(self, proposal: OptimizerProposal):
        """Publishes an optimizer proposal to the persistent queue."""
        proposal_key = f"proposal:{proposal.proposal_id}"
        self.storage.save_state(proposal_key, proposal.dict())

        pending_proposals = self.storage.load_state(PROPOSALS_PENDING_KEY) or []
        pending_proposals.append(proposal.proposal_id)
        self.storage.save_state(PROPOSALS_PENDING_KEY, pending_proposals)

        logging.info(f"Published proposal {proposal.proposal_id} to the event bus.")

    def subscribe_proposal(self) -> Optional[OptimizerProposal]:
        """
        Subscribes to an optimizer proposal, moving it from 'pending' to 'processing'.
        """
        pending_proposals = self.storage.load_state(PROPOSALS_PENDING_KEY) or []
        if not pending_proposals:
            return None

        proposal_id = pending_proposals.pop(0)
        self.storage.save_state(PROPOSALS_PENDING_KEY, pending_proposals)

        processing_proposals = self.storage.load_state(PROPOSALS_PROCESSING_KEY) or []
        processing_proposals.append(proposal_id)
        self.storage.save_state(PROPOSALS_PROCESSING_KEY, processing_proposals)

        proposal_data = self.storage.load_state(f"proposal:{proposal_id}")
        if proposal_data:
            logging.info(f"Subscribed to proposal {proposal_id} from the event bus.")
            return OptimizerProposal(**proposal_data)
        return None

    def acknowledge_proposal(self, proposal_id: str):
        """Removes a proposal from the 'processing' list after it's been audited."""
        processing_proposals = self.storage.load_state(PROPOSALS_PROCESSING_KEY) or []
        if proposal_id in processing_proposals:
            processing_proposals.remove(proposal_id)
            self.storage.save_state(PROPOSALS_PROCESSING_KEY, processing_proposals)
            # Optionally, delete the proposal data itself
            self.storage.delete_state(f"proposal:{proposal_id}")
            logging.debug(f"Acknowledged proposal {proposal_id}.")

    def publish_verdict(self, verdict: AuditVerdict):
        """Publishes an audit verdict."""
        verdict_key = f"{VERDICTS_KEY_PREFIX}{verdict.audit_id}"
        self.storage.save_state(verdict_key, verdict.dict())

        # Create an index for proposal_id -> verdict_id
        proposal_verdict_key = f"{VERDICTS_KEY_PREFIX}for_proposal:{verdict.proposal_id}"
        self.storage.save_state(proposal_verdict_key, verdict.audit_id)
        
        # Track the latest verdict
        self.storage.save_state(LATEST_VERDICT_ID_KEY, verdict.audit_id)

        logging.info(f"Published verdict {verdict.audit_id} for proposal {verdict.proposal_id}.")

    def subscribe_verdict(self, proposal_id: str) -> Optional[AuditVerdict]:
        """Subscribes to a verdict for a specific proposal."""
        proposal_verdict_key = f"{VERDICTS_KEY_PREFIX}for_proposal:{proposal_id}"
        verdict_id = self.storage.load_state(proposal_verdict_key)

        if not verdict_id:
            return None

        verdict_key = f"{VERDICTS_KEY_PREFIX}{verdict_id}"
        verdict_data = self.storage.load_state(verdict_key)

        if verdict_data:
            # After subscribing, we can remove the verdict and its index
            self.storage.delete_state(verdict_key)
            self.storage.delete_state(proposal_verdict_key)
            logging.info(f"Subscribed to verdict {verdict_id} for proposal {proposal_id}.")
            return AuditVerdict(**verdict_data)
        return None
        
    def get_latest_verdict(self) -> Optional[AuditVerdict]:
        """Retrieves the most recent audit verdict."""
        latest_verdict_id = self.storage.load_state(LATEST_VERDICT_ID_KEY)
        if not latest_verdict_id:
            return None
        
        verdict_key = f"{VERDICTS_KEY_PREFIX}{latest_verdict_id}"
        verdict_data = self.storage.load_state(verdict_key)
        if verdict_data:
            return AuditVerdict(**verdict_data)
        return None

    def publish_event(self, event_name: str):
        """Publishes a generic event."""
        event_key = f"{EVENTS_KEY_PREFIX}{event_name}"
        self.storage.save_state(event_key, {"timestamp": time.time()})
        logging.info(f"Published event '{event_name}'.")

    def wait_for_event(self, event_name: str, timeout: int = 10):
        """Waits for a specific event to be published."""
        start_time = time.time()
        event_key = f"{EVENTS_KEY_PREFIX}{event_name}"
        while True:
            if self.storage.load_state(event_key):
                # Clean up the event after it's been caught
                self.storage.delete_state(event_key)
                return
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timed out waiting for event '{event_name}'")
            time.sleep(1)

# Note: This refactored version assumes that the StorageInterface might have a `delete_state` method.
# If it doesn't, we can simply save `None` to the key to "delete" it.
# I will add a `delete_state` to the interface and implementation.
