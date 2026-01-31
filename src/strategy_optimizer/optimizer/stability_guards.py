import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple


class StabilityGuards:
    """
    Implements freeze, rollback, and memory guards for parameter stability.
    Follows spec section 3.3.1 "Learning Memory & Stability Guards"

    Freeze Logic:
    - If profit > 5% and drawdown decreases for 3 consecutive iterations,
      freeze parameters for N iterations (default: 5)

    Rollback Logic:
    - If drawdown increases by more than 15% in a single iteration,
      revert to last stable configuration

    Fallback Logic:
    - If AI API fails, apply deterministic heuristic adjustments

    Learning Memory:
    - Persistent tracking of tested parameter sets
    - Per-regime performance statistics
    - Blacklisting of parameter sets with drawdown > 40%
    """

    def __init__(self, config, state_manager=None, parameter_memory=None):
        self.config = config
        self.state_manager = state_manager
        self.parameter_memory = parameter_memory

        # Spec 3.3.1: Freeze, Rollback, and Fallback thresholds
        stability_cfg = config.get("stability_guards", config.get("stability", {}))

        self.freeze_profit_threshold = stability_cfg.get("freeze_profit_threshold", 5.0)
        self.freeze_consecutive_iterations = stability_cfg.get(
            "consecutive_improving_for_freeze", 3
        )
        self.freeze_duration = stability_cfg.get("freeze_duration", 5)
        self.rollback_drawdown_threshold = stability_cfg.get(
            "rollback_drawdown_spike", 15.0
        )
        self.blacklist_drawdown_threshold = stability_cfg.get(
            "blacklist_drawdown_threshold", 40.0
        )

        # State tracking
        self.freeze_state = (
            None  # None, or {'until_iteration': N, 'frozen_params': {...}}
        )
        self.rollback_stack = []  # List of (iteration, params, metrics) tuples
        self.performance_history = []  # Tracking for consecutive improvements
        self.stability_state = "NORMAL"  # NORMAL, FROZEN, RECOVERY
        self.last_stable_params = None
        self.stability_history = []  # Log of stability state changes

        logging.info("Initialized StabilityGuards with spec thresholds:")
        logging.info(f"  Freeze profit threshold: {self.freeze_profit_threshold}%")
        logging.info(f"  Freeze duration: {self.freeze_duration} iterations")
        logging.info(
            f"  Consecutive improving for freeze: {self.freeze_consecutive_iterations}"
        )
        logging.info(f"  Rollback drawdown spike: {self.rollback_drawdown_threshold}%")
        logging.info(
            f"  Blacklist drawdown threshold: {self.blacklist_drawdown_threshold}%"
        )

        if state_manager:
            self._initialize_tables()

    def _initialize_tables(self):
        """Create necessary database tables for state persistence."""
        if not self.state_manager:
            return

        try:
            self.state_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS stability_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iteration INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    frozen_params TEXT,
                    rollback_params TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            self.state_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS rollback_stack (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iteration INTEGER NOT NULL,
                    params TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            logging.info("Stability state tables initialized.")
        except Exception as e:
            logging.warning(f"Could not initialize stability tables: {e}")

    def check_freeze(
        self, iteration: int, current_profit: float, current_drawdown: float
    ) -> bool:
        """
        Spec 3.3.1: Freeze Logic

        If profit > 5% AND drawdown decreases for 3 consecutive iterations,
        freeze parameters for N iterations (default: 5)

        Returns True if parameters should be frozen.
        """
        # Check if currently in freeze period
        if self.freeze_state is not None:
            if iteration >= self.freeze_state["until_iteration"]:
                logging.info(f"Freeze period expired at iteration {iteration}")
                self.freeze_state = None
                self.stability_state = "NORMAL"
                self._record_stability_change(
                    "NORMAL", iteration, "Freeze period expired"
                )
            else:
                freeze_countdown = self.freeze_state["until_iteration"] - iteration
                logging.info(
                    f"Parameters frozen: {freeze_countdown} iterations remaining"
                )
                return True

        # Check freeze conditions
        if current_profit > self.freeze_profit_threshold:
            # Track performance history
            self.performance_history.append(
                {
                    "iteration": iteration,
                    "profit": current_profit,
                    "drawdown": current_drawdown,
                }
            )

            # Keep only relevant history
            if len(self.performance_history) > self.freeze_consecutive_iterations + 1:
                self.performance_history = self.performance_history[
                    -(self.freeze_consecutive_iterations + 1) :
                ]

            # Check for consecutive drawdown decreases
            if len(self.performance_history) >= self.freeze_consecutive_iterations:
                recent = self.performance_history[-self.freeze_consecutive_iterations :]
                drawdowns = [r["drawdown"] for r in recent]

                # All values must be strictly decreasing
                is_decreasing = all(
                    drawdowns[i] >= drawdowns[i + 1] for i in range(len(drawdowns) - 1)
                )

                if (
                    is_decreasing and len(set(drawdowns)) > 1
                ):  # Avoid trivial case of all same values
                    logging.warning(
                        f"FREEZE ACTIVATED at iteration {iteration}: "
                        f"profit={current_profit:.2f}%, drawdown decreasing {drawdowns}"
                    )
                    self.freeze_state = {
                        "start_iteration": iteration,
                        "until_iteration": iteration + self.freeze_duration,
                        "freeze_profit": current_profit,
                        "freeze_drawdown": current_drawdown,
                    }
                    self.stability_state = "FROZEN"
                    self._record_stability_change(
                        "FROZEN",
                        iteration,
                        f"Profit {current_profit:.2f}% > {self.freeze_profit_threshold}%, drawdown decreasing",
                    )
                    return True
        else:
            # Reset performance history if profit condition not met
            self.performance_history = []

        return False

    def check_rollback(
        self, iteration: int, current_drawdown: float, previous_drawdown: float
    ) -> Optional[Dict]:
        """
        Spec 3.3.1: Rollback Logic

        If drawdown increases by more than 15% in a single iteration,
        revert to last known stable configuration.

        Returns rolled-back parameters if triggered, None otherwise.
        """
        drawdown_increase = current_drawdown - previous_drawdown

        if (
            drawdown_increase > self.rollback_drawdown_threshold
            and self.last_stable_params
        ):
            logging.error(
                f"ROLLBACK TRIGGERED at iteration {iteration}: "
                f"drawdown increased by {drawdown_increase:.2f}% "
                f"(threshold: {self.rollback_drawdown_threshold}%)"
            )

            self.stability_state = "RECOVERY"
            self._record_stability_change(
                "RECOVERY", iteration, f"Drawdown spike: +{drawdown_increase:.2f}%"
            )

            return self.last_stable_params.copy()

        return None

    def record_stable_state(self, iteration: int, params: Dict, metrics: Dict):
        """
        Record a stable parameter/metric combination for potential rollback.
        Spec 3.3.1: Record stable state when profit > 0 and drawdown is good.
        """
        self.last_stable_params = params.copy()
        self.rollback_stack.append((iteration, params.copy(), metrics.copy()))

        # Keep only recent history (last 10 stable states)
        if len(self.rollback_stack) > 10:
            self.rollback_stack = self.rollback_stack[-10:]

        profit = metrics.get("profit", 0)
        drawdown = metrics.get("max_drawdown_pct", 0)
        params_hash = self._hash_params(params)

        logging.info(
            f"Recorded stable state at iteration {iteration}: "
            f"profit={profit:.2f}%, drawdown={drawdown:.2f}%, params_hash={params_hash}"
        )

        # Transition from RECOVERY to NORMAL if performance is good
        if self.stability_state == "RECOVERY" and profit > 0 and drawdown < 20:
            self.stability_state = "NORMAL"
            self._record_stability_change(
                "NORMAL", iteration, "Recovered to good performance"
            )

    def check_blacklist(self, params: Dict, drawdown: float) -> bool:
        """
        Spec 3.3.1: Blacklist parameter sets with drawdown > 40%

        Returns True if should be blacklisted, False otherwise.
        """
        if drawdown > self.blacklist_drawdown_threshold:
            params_hash = self._hash_params(params)
            logging.warning(
                f"BLACKLISTING parameter set {params_hash}: "
                f"drawdown {drawdown:.2f}% > {self.blacklist_drawdown_threshold}%"
            )

            if self.parameter_memory:
                self.parameter_memory.blacklist(
                    params_hash,
                    reason=f"Drawdown > {self.blacklist_drawdown_threshold}%",
                )

            return True

        return False

    def get_frozen_params(self) -> Optional[Dict]:
        """
        If parameters are currently frozen, return the frozen parameters.
        """
        if self.freeze_state is not None:
            return self.freeze_state.get("frozen_params", None)
        return None

    def get_stability_state(self) -> str:
        """
        Return current stability state: NORMAL, FROZEN, or RECOVERY.
        """
        return self.stability_state

    def get_freeze_countdown(self, current_iteration: int) -> int:
        """Return iterations remaining in freeze period, or 0 if not frozen"""
        if self.freeze_state is not None:
            countdown = max(
                0, self.freeze_state.get("until_iteration", 0) - current_iteration
            )
            return countdown
        return 0

    def get_stability_info(self) -> Dict:
        """
        Return detailed stability information for UI/monitoring.
        """
        info = {
            "state": self.get_stability_state(),
            "frozen": self.freeze_state is not None,
            "freeze_countdown": self.get_freeze_countdown(0),
            "rollback_available": len(self.rollback_stack) > 0,
            "has_stable_params": self.last_stable_params is not None,
            "history": self.stability_history[-10:],  # Last 10 state changes
        }

        return info

    def _hash_params(self, params: Dict) -> str:
        """Create deterministic hash of parameters"""
        params_str = json.dumps(params, sort_keys=True, default=str)
        return hashlib.md5(params_str.encode()).hexdigest()[:8]

    def _record_stability_change(
        self, new_state: str, iteration: int, reason: str = ""
    ) -> None:
        """Log a stability state change event"""
        self.stability_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "iteration": iteration,
                "state": new_state,
                "reason": reason,
            }
        )
        logging.info(f"Stability state: {new_state} @ iteration {iteration} - {reason}")

        if self.state_manager:
            try:
                query = """
                    INSERT INTO stability_state (iteration, status)
                    VALUES (?, ?)
                """
                self.state_manager.execute_query(query, (iteration, new_state))
            except Exception as e:
                logging.debug(f"Could not log to DB: {e}")

    def apply_heuristic_update(self, current_params: Dict, regime: str) -> Dict:
        """
        Apply deterministic heuristic parameter adjustments when LLM is unavailable.

        Heuristic rules:
        - Increase min_score by 0.2 if too many losing trades
        - Decrease stop_multiplier by 0.2 if drawdown is high
        - Adjust risk_pct based on win rate
        """
        adjusted = current_params.copy()

        if regime == "RANGE":
            # In ranging markets, be more selective
            adjusted["min_score"] = min(adjusted.get("min_score", 3.0) + 0.2, 5.0)
        elif regime == "TREND":
            # In trending markets, relax entry criteria slightly
            adjusted["min_score"] = max(adjusted.get("min_score", 3.0) - 0.1, 1.0)
        elif regime == "HIGH_VOL":
            # In high volatility, reduce position size
            adjusted["risk_pct"] = max(adjusted.get("risk_pct", 1.0) - 0.25, 0.25)
            adjusted["stop_multiplier"] = min(
                adjusted.get("stop_multiplier", 2.0) + 0.2, 3.0
            )

        logging.info(f"Applied heuristic update for {regime} regime: {adjusted}")
        return adjusted
