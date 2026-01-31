import logging
import random

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
        Perturbs parameters and scores them using rapid backtesting to find a better set.
        """
        logging.warning("LLM failed, using deterministic fallback mode.")
        
        best_params = current_params
        # Run a baseline backtest to get the current score
        baseline_result = self.backtest_engine.rapid_backtest(symbol, end_date, current_params)
        if not baseline_result:
            return self.revert_to_safe_baseline()

        best_score = baseline_result.profit_factor - 2 * abs(baseline_result.max_drawdown_pct)
        
        # Iterate through each parameter and test perturbations
        for param_to_perturb in current_params.keys():
            if param_to_perturb not in self.parameter_bounds:
                continue

            param_range = self.parameter_bounds[param_to_perturb]['max'] - self.parameter_bounds[param_to_perturb]['min']
            delta = 0.05 * param_range
            
            # Create variants (+delta, -delta)
            plus_variant = current_params.copy()
            plus_variant[param_to_perturb] += delta
            plus_variant[param_to_perturb] = max(
                self.parameter_bounds[param_to_perturb]['min'],
                min(self.parameter_bounds[param_to_perturb]['max'], plus_variant[param_to_perturb])
            )

            minus_variant = current_params.copy()
            minus_variant[param_to_perturb] -= delta
            minus_variant[param_to_perturb] = max(
                self.parameter_bounds[param_to_perturb]['min'],
                min(self.parameter_bounds[param_to_perturb]['max'], minus_variant[param_to_perturb])
            )

            for variant_params in [plus_variant, minus_variant]:
                # Score the variant using rapid backtesting
                result = self.backtest_engine.rapid_backtest(symbol, end_date, variant_params)
                if result:
                    score = result.profit_factor - 2 * abs(result.max_drawdown_pct)
                    if score > best_score:
                        best_score = score
                        best_params = variant_params
                        logging.info(f"Found better parameters in fallback mode: score={score:.2f}, params={best_params}")

        return best_params

    def revert_to_safe_baseline(self) -> dict:
        """Returns the safe baseline parameters."""
        logging.warning("Reverting to safe baseline parameters.")
        return self.safe_baseline