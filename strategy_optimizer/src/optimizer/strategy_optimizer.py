import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from data_bus.schemas import OptimizerProposal, CausalChainRef

class StrategyOptimizer:
    """
    Main optimization logic with stability guards and learning memory.
    Generates parameter proposals following the spec output schema.
    """
    def __init__(self, config, regime_classifier, llm_interface, fallback_mode, parameter_memory, event_bus, stability_guards=None):
        self.config = config
        self.regime_classifier = regime_classifier
        self.llm_interface = llm_interface
        self.fallback_mode = fallback_mode
        self.parameter_memory = parameter_memory
        self.event_bus = event_bus
        self.stability_guards = stability_guards
        self.proposal_version = 0
        self.previous_metrics = None
        self.previous_proposal_id = None
        logging.info("Initialized StrategyOptimizer.")

    def propose_parameters(
        self,
        iteration: int,
        current_metrics: dict,
        regime: str,
        per_regime_metrics: dict,
        symbol: str,
        end_date: str
    ) -> Tuple[Dict, str, str]:  # (params, action, reasoning)
        """
        Generates a new parameter proposal following the spec.
        
        Returns:
            Tuple of (proposed_parameters, action, reasoning)
            where action is one of: UPDATE, HOLD, ROLLBACK
        """
        logging.info(f"Iteration {iteration}: Generating parameter proposal for regime: {regime}")

        # 0. Check if currently frozen
        if self.stability_guards:
            current_drawdown = current_metrics.get('max_drawdown_pct', 0)
            prev_drawdown = self.previous_metrics.get('max_drawdown_pct', 0) if self.previous_metrics else current_drawdown
            
            # Check freeze
            is_frozen = self.stability_guards.check_freeze(
                iteration,
                current_metrics.get('profit', 0),
                current_drawdown
            )
            
            if is_frozen:
                logging.info("Parameters are frozen, returning HOLD")
                return self.config.get('safe_baseline', {}), 'HOLD', 'Parameters frozen for stability'
            
            # Check rollback
            rollback_params = self.stability_guards.check_rollback(
                iteration,
                current_drawdown,
                prev_drawdown
            )
            
            if rollback_params:
                logging.warning("Rollback triggered due to drawdown spike")
                return rollback_params, 'ROLLBACK', 'Rolled back due to drawdown increase > 15%'

        # 1. Build optimization context for LLM
        current_params = current_metrics.get('parameters', self.config.get('safe_baseline', {}))
        
        # Check if parameter set has been tested before
        tested_before = self.parameter_memory.has_been_tested(current_params, regime) if self.parameter_memory else False
        if tested_before:
            logging.info(f"Parameters tested before in {regime} regime")

        # Count regimes with improvement
        improved_regimes = 0
        if self.previous_metrics:
            prev_global_profit = self.previous_metrics.get('profit', 0)
            curr_global_profit = current_metrics.get('profit', 0)
            if curr_global_profit > prev_global_profit:
                improved_regimes += 1

        optimization_context = {
            'regime_label': regime,
            'regime_confidence': current_metrics.get('regime_confidence', 0.8),
            'stability_state': self.stability_guards.get_stability_state() if self.stability_guards else 'NORMAL',
            'current_parameters': current_params,
            'global_profit': current_metrics.get('profit', 0),
            'global_max_drawdown': current_metrics.get('max_drawdown_pct', 0),
            'global_win_rate': current_metrics.get('win_rate', 0),
            'global_total_trades': current_metrics.get('total_trades', 0),
            'global_profit_factor': current_metrics.get('profit_factor', 0),
            'per_regime_metrics': per_regime_metrics,
            'best_parameters': self.parameter_memory.get_best_params(regime) if self.parameter_memory else {},
            'improved_regimes': improved_regimes,
            'drawdown_decreasing': (
                self.previous_metrics and
                current_metrics.get('max_drawdown_pct', 0) < self.previous_metrics.get('max_drawdown_pct', 0)
            ) if self.previous_metrics else False
        }

        # 2. Try to get proposal from LLM
        prompt = f"""Optimize trading parameters for {regime} regime.

Current state:
- Profit: {current_metrics.get('profit', 0):.2f}%
- Drawdown: {current_metrics.get('max_drawdown_pct', 0):.2f}%
- Win Rate: {current_metrics.get('win_rate', 0):.2f}%
- Trades: {current_metrics.get('total_trades', 0)}

Suggest parameter adjustments or hold current parameters."""

        llm_response = self.llm_interface.query_llm(prompt, optimization_context) if self.llm_interface else None

        # 3. If LLM fails, use fallback mode
        if not llm_response:
            logging.warning("LLM failed or unavailable, using fallback mode")
            proposed_params = self.fallback_mode.perturb_parameters(current_params, 'BTC/USDT', end_date) if self.fallback_mode else current_params
            action = 'UPDATE'
            reasoning = 'Applied heuristic adjustments due to LLM unavailability'
        else:
            proposed_params = llm_response.get('params', current_params)
            action = llm_response.get('action', 'HOLD')
            reasoning = llm_response.get('reasoning', 'No reasoning provided')

        # 4. Log the tested parameters
        if self.parameter_memory:
            self.parameter_memory.log_tested(proposed_params if action == 'UPDATE' else current_params, regime, current_metrics, action)

        # 5. Record stable state if metrics are good
        if self.stability_guards and current_metrics.get('profit', 0) > 0:
            self.stability_guards.record_stable_state(iteration, current_params, current_metrics)

        # Store for next iteration
        self.previous_metrics = current_metrics.copy()
        self.proposal_version += 1

        logging.info(f"Proposal generated: action={action}, version={self.proposal_version}")
        return proposed_params, action, reasoning

    def publish_proposal(self, params: Dict, action: str) -> OptimizerProposal:
        """
        Publishes a parameter proposal to the event bus.
        """
        proposal = OptimizerProposal(
            proposal_version=self.proposal_version,
            source="StrategyOptimizer_v2",
            proposed_parameters=params,
            context={
                "action": action,
                "timestamp": datetime.now().isoformat()
            },
            causal_chain_refs=[]
        )
        
        if self.event_bus:
            self.event_bus.publish_proposal(proposal)
        
        self.previous_proposal_id = proposal.proposal_id
        logging.info(f"Published proposal {proposal.proposal_id}: {action}")
        return proposal
