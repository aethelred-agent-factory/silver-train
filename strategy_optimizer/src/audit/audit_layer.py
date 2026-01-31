import logging
from data_bus.schemas import OptimizerProposal, AuditVerdict, TieredFinding, AuditAction
from data_bus.event_bus import EventBus
import time

class AuditLayer:
    """
    Main audit coordinator. Subscribes to proposals, runs checks, and generates verdicts.
    """
    def __init__(self, config, event_bus, t1_checks, t2_checks, t3_checks, causal_chain_validator, artifact_store):
        self.config = config
        self.event_bus = event_bus
        self.t1_checks = t1_checks
        self.t2_checks = t2_checks
        self.t3_checks = t3_checks
        self.causal_chain_validator = causal_chain_validator
        self.artifact_store = artifact_store
        logging.info("Initialized AuditLayer.")

    def audit_proposal(self, proposal: OptimizerProposal) -> AuditVerdict:
        """
        Runs all T1, T2, and T3 checks on a proposal and generates a verdict.
        """
        logging.info(f"Auditing proposal {proposal.proposal_id}")
        
        findings = []
        
        # Run checks
        findings.extend(self.t1_checks.run_all(proposal))
        findings.extend(self.t2_checks.run_all(proposal))
        findings.extend(self.t3_checks.run_all(proposal))
        
        # Validate causal chain
        if not self.causal_chain_validator.validate_proposal(proposal):
            findings.append(TieredFinding(
                tier="T2",
                code="T2_CausalGap",
                explanation="Causal chain validation failed. An artifact was missing, corrupt, or from the future."
            ))

        # Generate verdict
        verdict = self.generate_verdict(proposal, findings)
        
        # Store artifact and get the updated verdict with artifact_refs and checksum
        final_verdict = self.artifact_store.store_artifact(verdict)
        
        # Publish verdict
        self.event_bus.publish_verdict(final_verdict)
        
        return final_verdict

    def generate_verdict(self, proposal: OptimizerProposal, findings: list[TieredFinding]) -> AuditVerdict:
        """
        Generates a final verdict based on the findings.
        """
        action_type = "ALLOW"
        restrictions = {}
        
        # T1 findings immediately result in a BLOCK
        if any(f.tier == "T1" for f in findings):
            action_type = "BLOCK"
            t1_reasons = [f.code for f in findings if f.tier == "T1"]
            restrictions['reason'] = t1_reasons[0] if t1_reasons else "T1 failure"
        # T2 findings result in RESTRICTION
        elif any(f.tier == "T2" for f in findings):
            action_type = "ALLOW_WITH_RESTRICTION"
            # Aggregate restrictions from all T2 findings
            if any(f.code == "T2_InsufficientSample" for f in findings):
                restrictions['max_order_size_pct'] = 0.25
            if any(f.code == "T2_FuzzyBoundary" for f in findings):
                restrictions['parameter_change_max_pct'] = 0.05
            if 'reason' not in restrictions:
                t2_reasons = [f.code for f in findings if f.tier == "T2"]
                restrictions['reason'] = f"T2 flags: {', '.join(t2_reasons)}"

        return AuditVerdict(
            proposal_id=proposal.proposal_id,
            tiered_findings=findings,
            action=AuditAction(type=action_type, restrictions=restrictions if restrictions else None),
            artifact_refs=[], # Populated by the artifact_store
            checksum="" # Populated by the artifact_store
        )
        
    def listen_for_proposals(self):
        """
        Continuously listens for proposals on the event bus and audits them.
        This function is designed to be run in a background thread.
        """
        logging.info("AuditLayer is listening for proposals.")
        while True:
            try:
                proposal = self.event_bus.subscribe_proposal()
                if proposal:
                    # Wait for the artifact_created event
                    self.event_bus.wait_for_event("artifact_created")
                    self.audit_proposal(proposal)
                else:
                    # Sleep when the queue is empty to prevent busy-waiting
                    time.sleep(2)
            except Exception as e:
                logging.error(f"Error in audit listener loop: {e}", exc_info=True)
                time.sleep(5) # Wait a bit longer after an error
