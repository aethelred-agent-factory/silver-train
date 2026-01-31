import logging
import random
import numpy as np

class FallbackMode:
    """
    Provides a deterministic method for parameter perturbation when the LLM fails.
    """
    def __init__(self, config, backtest_engine):
        self.config = config
        self.backtest_engine = backtest_engine # Used for rapid simulation
        self.parameter_bounds = config['parameter_bounds']
        self.safe_baseline = config['safe_baseline']
        logging.info("Initialized FallbackMode.")

    def perturb_parameters(self, current_params: dict, symbol: str, end_date: str) -> dict:
        """
        Perturbs parameters more aggressively to find higher profit configurations.
        Uses rapid backtesting to score variants. Validates that results are realistic.
        """
        logging.warning("LLM failed, using deterministic fallback mode.")
        
        best_params = current_params
        # Run a baseline backtest to get the current score
        baseline_result = self.backtest_engine.rapid_backtest(symbol, end_date, current_params)
        if not baseline_result:
            return self.revert_to_safe_baseline()

        # Validate baseline result is realistic (need minimum trades for statistical relevance)
        if baseline_result.total_trades < 3 or np.isinf(baseline_result.profit_factor):
            logging.warning(f"Baseline result is invalid (<3 trades or inf profit), reverting to safe baseline")
            return self.revert_to_safe_baseline()
        
        # Score prioritizes profit heavily for 25% target achievement
        best_score = baseline_result.profit_factor * 100 - 3 * abs(baseline_result.max_drawdown_pct)
        logging.info(f"Baseline score: {best_score:.2f} (profit_factor={baseline_result.profit_factor:.2f}, trades={baseline_result.total_trades})")
        
        # Iterate through each parameter with MORE aggressive perturbations
        for param_to_perturb in current_params.keys():
            if param_to_perturb not in self.parameter_bounds:
                continue

            param_range = self.parameter_bounds[param_to_perturb]['max'] - self.parameter_bounds[param_to_perturb]['min']
            # More aggressive: test larger deltas (10%, 15%, 20% of range)
            deltas = [0.10 * param_range, 0.15 * param_range, 0.20 * param_range]
            
            # Create variants with larger perturbations
            for delta in deltas:
                for sign in [1, -1]:
                    variant_params = current_params.copy()
                    variant_params[param_to_perturb] += sign * delta
                    variant_params[param_to_perturb] = max(
                        self.parameter_bounds[param_to_perturb]['min'],
                        min(self.parameter_bounds[param_to_perturb]['max'], variant_params[param_to_perturb])
                    )

                    # Skip if unchanged
                    if variant_params[param_to_perturb] == current_params[param_to_perturb]:
                        continue
                    
                    # Score the variant using rapid backtesting
                    result = self.backtest_engine.rapid_backtest(symbol, end_date, variant_params)
                    # CRITICAL: Require minimum 3 trades for statistical relevance, no inf values
                    if result and result.total_trades >= 3 and not np.isinf(result.profit_factor):
                        # Weighted scoring: profit * 100 + win_rate * 0.5 - drawdown * 3
                        score = (result.profit_factor * 100) + (result.win_rate * 0.5) - (3 * abs(result.max_drawdown_pct))
                        if score > best_score:
                            best_score = score
                            best_params = variant_params
                            logging.info(f"Found better params: profit={result.profit_factor*100-100:.2f}%, trades={result.total_trades}, score={score:.2f}, param {param_to_perturb}={variant_params[param_to_perturb]:.4f}")
                    elif result and (result.total_trades < 3 or np.isinf(result.profit_factor)):
                        logging.debug(f"Skipping invalid variant: {param_to_perturb}={variant_params[param_to_perturb]:.4f} (trades={result.total_trades} or inf)")

        return best_params

    def revert_to_safe_baseline(self) -> dict:
        """Returns the safe baseline parameters."""
        logging.warning("Reverting to safe baseline parameters.")
        return self.safe_baseline