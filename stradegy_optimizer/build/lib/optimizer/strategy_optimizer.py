import logging
from datetime import datetime

from data_bus.schemas import OptimizerProposal

class StrategyOptimizer:
    """
    Main optimization logic, parameter proposals.
    """
    def __init__(self, config, regime_classifier, llm_interface, fallback_mode, parameter_memory, event_bus):
        self.config = config
        self.regime_classifier = regime_classifier
        self.llm_interface = llm_interface
        self.fallback_mode = fallback_mode
        self.parameter_memory = parameter_memory
        self.event_bus = event_bus
        self.proposal_version = 0
        logging.info("Initialized StrategyOptimizer.")

    def propose_parameters(self, current_metrics: dict, regime: str, history: dict, symbol: str, end_date: str) -> OptimizerProposal:
        """
        Generates a new parameter proposal and publishes it to the event bus.
        """
        logging.info(f"Generating new parameter proposal for regime: {regime}")

        # 1. Check parameter memory to avoid repetition
        # Note: a more sophisticated check is needed here
        # if self.parameter_memory.has_been_tested(proposed_params, regime):
        #     logging.warning("Parameter set has been tested before, trying a new one.")
        #     # Logic to generate a different set of parameters
        #     pass

        # 2. Try to get proposal from LLM
        prompt = f"Generate a new set of strategy parameters for the current market regime: {regime}"
        proposed_params = self.llm_interface.query_llm(prompt, current_metrics)
        
        # 3. If LLM fails, use fallback mode
        if not proposed_params:
            logging.warning("LLM failed, using fallback mode.")
            current_params = current_metrics.get('parameters', self.config['safe_baseline'])
            proposed_params = self.fallback_mode.perturb_parameters(current_params, symbol, end_date)

        self.proposal_version += 1
        
        proposal = OptimizerProposal(
            proposal_version=self.proposal_version,
            source="StrategyOptimizer_v1",
            proposed_parameters=proposed_params,
            context={
                "regime_label": regime,
                "regime_confidence": current_metrics.get('regime_confidence', 0.8),
                "data_snapshot_range": {"start": "2025-01-01T00:00:00Z", "end": "2025-01-30T23:00:00Z"},
                "metrics_snapshot": current_metrics
            },
            causal_chain_refs=[] # To be populated with actual evidence
        )
        
        # Publish the proposal to the event bus
        self.event_bus.publish_proposal(proposal)
        logging.info(f"Published proposal {proposal.proposal_id}")
        
        return proposal

    def apply_frozen_epoch(self):
        """
        Enforce minimum iterations before change. (Placeholder)
        """
        logging.info("Checking frozen epoch rules...")
        # This would check the state to see if enough time/iterations have passed
        # before allowing another parameter change.
        pass
