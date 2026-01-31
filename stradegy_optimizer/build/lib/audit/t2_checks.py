import logging
from data_bus.schemas import OptimizerProposal, TieredFinding

class T2Checks:
    """
    Tier 2 checks for reasoning flaws and confidence degradation.
    """
    def __init__(self, config):
        self.config = config
        self.audit_rules = config['audit_rules']['T2']
        self.regime_config = config['regime_config']
        logging.info("Initialized T2Checks.")

    def check_insufficient_sample(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Checks if the strategy acceptance is based on a small number of trades.
        """
        n_trades = proposal.context.get('metrics_snapshot', {}).get('trades_sample', 0)
        n_min = 100 # As per the spec
        
        if n_trades < n_min:
            rule = self.audit_rules[0]
            return TieredFinding(
                tier="T2",
                code=rule['name'],
                explanation=f"Trades in sample (N={n_trades}) < configured N_min ({n_min})"
            )
        return None

    def check_fuzzy_boundary(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Checks if the regime classification is ambiguous (close to a threshold).
        """
        context = proposal.context
        # This is a placeholder for a real check logic.
        # It would require access to the indicator data.
        # We simulate it by checking the regime confidence.
        if context.get('regime_confidence', 1.0) < 0.7:
             rule = self.audit_rules[1]
             return TieredFinding(
                tier="T2",
                code=rule['name'],
                explanation=f"Regime confidence ({context.get('regime_confidence')}) is low."
            )
        return None

    def check_causal_gap(self, proposal: OptimizerProposal) -> TieredFinding:
        """
        Checks for missing causal chain.
        """
        if not proposal.causal_chain_refs:
            return TieredFinding(
                tier="T2",
                code="T2_CausalGap",
                explanation="Proposal is missing a causal chain."
            )
        return None

    def run_all(self, proposal: OptimizerProposal) -> list[TieredFinding]:
        """
        Runs all T2 checks on a proposal.
        """
        logging.info(f"Running T2 checks for proposal {proposal.proposal_id}")
        findings = []
        
        insufficient_sample = self.check_insufficient_sample(proposal)
        if insufficient_sample:
            findings.append(insufficient_sample)
            
        fuzzy_boundary = self.check_fuzzy_boundary(proposal)
        if fuzzy_boundary:
            findings.append(fuzzy_boundary)
            
        causal_gap = self.check_causal_gap(proposal)
        if causal_gap:
            findings.append(causal_gap)
            
        return findings
