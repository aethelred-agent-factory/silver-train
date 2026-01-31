import logging

from data_bus.schemas import OptimizerProposal, TieredFinding


class T3Checks:
    """
    Tier 3 checks for informational gaps and remediation requests.
    """

    def __init__(self, config):
        self.config = config
        self.audit_rules = config["audit_rules"]["T3"]
        logging.info("Initialized T3Checks.")

    def check_config_gaps(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Checks for missing required configuration keys.
        """
        # This is a placeholder. A real implementation would check
        # if all necessary configs for the proposed strategy are present.
        if "liquidity_thresholds" not in self.config:
            rule = self.audit_rules[0]
            return TieredFinding(
                tier="T3",
                code=rule["name"],
                explanation="Missing 'liquidity_thresholds' in system_config.yaml.",
            )
        return None

    def check_ambiguous_logs(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Performs an NLP check for vague terms in logs related to the proposal.
        (This is a highly simplified placeholder)
        """
        # A real implementation would require access to logs and an NLP model.
        # We simulate this by checking for a dummy flag in the context.
        if proposal.context.get("has_ambiguous_logs", False):
            rule = self.audit_rules[1]
            return TieredFinding(
                tier="T3",
                code=rule["name"],
                explanation="Ambiguous terms detected in logs related to this proposal.",
            )
        return None

    def run_all(self, proposal: OptimizerProposal) -> list[TieredFinding]:
        """
        Runs all T3 checks on a proposal.
        """
        logging.info(f"Running T3 checks for proposal {proposal.proposal_id}")
        findings = []

        config_gaps = self.check_config_gaps(proposal)
        if config_gaps:
            findings.append(config_gaps)

        ambiguous_logs = self.check_ambiguous_logs(proposal)
        if ambiguous_logs:
            findings.append(ambiguous_logs)

        return findings
