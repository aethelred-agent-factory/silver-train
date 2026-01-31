import logging

from data_bus.schemas import AuditVerdict, OptimizerProposal
from execution.order_manager import OrderManager


class ExecutionEngine:
    """
    Safe interface to exchange API for trade execution.
    Enforces three mandatory safety gates: Capital, Risk, and Governance.
    """

    def __init__(
        self, config, order_manager: OrderManager, state_manager, portfolio_state=None
    ):
        self.config = config
        self.order_manager = order_manager
        self.state_manager = state_manager
        self.portfolio_state = portfolio_state
        logging.info("Initialized ExecutionEngine.")

    def execute_trade(
        self, signal: dict, proposal: OptimizerProposal, audit_verdict: AuditVerdict
    ) -> bool:
        """
        Executes a trade after passing through exactly three mandatory safety checks.
        """
        # GLOBAL KILL SWITCH (Step 5)
        if self.state_manager.is_kill_switch_active():
            logging.critical("Execution HALTED by Global Kill Switch.")
            return False

        logging.info(
            f"Attempting to execute trade for {signal.get('symbol')} | Proposal: {proposal.proposal_id}"
        )

        # MANDATORY GATES (Step 3)
        try:
            # 1. Capital Exposure Check
            if not self._check_capital_exposure(signal):
                logging.error("FAILED: Capital Exposure Check")
                return False

            # 2. Risk Constraint Check
            if not self._check_risk_constraints():
                logging.error("FAILED: Risk Constraint Check")
                return False

            # 3. Governance Approval Check
            if not self._check_governance_approval(audit_verdict):
                logging.error("FAILED: Governance Approval Check")
                return False
        except Exception as e:
            logging.critical(f"UNCERTAINTY IN SAFETY GATES: {e}. Blocking execution.")
            return False

        # Proceed to execution
        symbol = signal.get("symbol", "BTC/USDT")
        side = "buy" if signal.get("signal", 0) == 1 else "sell"
        amount = signal.get("amount", 0.0)
        price = signal.get("price")

        # Apply restrictions if applicable
        action_type = ""
        restrictions = None
        if hasattr(audit_verdict, "action"):  # Pydantic object
            action_type = audit_verdict.action.type
            restrictions = audit_verdict.action.restrictions
        else:  # Dictionary (fallback)
            action_type = audit_verdict.get("action", {}).get("type")
            restrictions = audit_verdict.get("action", {}).get("restrictions")

        if action_type == "ALLOW_WITH_RESTRICTION" and restrictions:
            max_order_size_pct = restrictions.get("max_order_size_pct", 1.0)
            amount *= max_order_size_pct

        try:
            order_id = self.order_manager.place_order(
                symbol, side, amount, proposal, price=price
            )
            return bool(order_id)
        except Exception as e:
            logging.error(f"Execution failed: {e}")
            return False

    def _check_capital_exposure(self, signal: dict) -> bool:
        """GATE 1: Ensures trade size does not exceed exposure limits."""
        if not self.portfolio_state:
            logging.error("Capital exposure check FAILED: PortfolioState missing.")
            return False  # Fail closed

        max_exposure = (
            self.config.get("system_config", {})
            .get("risk", {})
            .get("max_capital_exposure_pct", 20.0)
        )
        current_metrics = self.portfolio_state.get_metrics()

        trade_value = signal.get("amount", 0) * signal.get("price", 0)
        total_value = current_metrics["current_equity"]

        exposure_pct = (trade_value / total_value * 100) if total_value > 0 else 100

        if exposure_pct > max_exposure:
            logging.warning(
                f"Capital Exposure ({exposure_pct:.2f}%) exceeds limit ({max_exposure}%)"
            )
            return False
        return True

    def _check_risk_constraints(self) -> bool:
        """GATE 2: Ensures portfolio risk metrics (e.g. drawdown) are within bounds."""
        if not self.portfolio_state:
            logging.error("Risk constraint check FAILED: PortfolioState missing.")
            return False  # Fail closed

        max_drawdown = (
            self.config.get("system_config", {})
            .get("risk", {})
            .get("max_drawdown_limit_pct", 15.0)
        )
        current_drawdown = self.portfolio_state.max_drawdown_pct

        if current_drawdown > max_drawdown:
            logging.warning(
                f"Portfolio Drawdown ({current_drawdown:.2f}%) exceeds limit ({max_drawdown}%)"
            )
            return False
        return True

    def _check_governance_approval(self, audit_verdict: AuditVerdict) -> bool:
        """GATE 3: Validates independent audit and manual kill-switch/approval."""
        # Handle both Pydantic model and dictionary for robustness
        if hasattr(audit_verdict, "action"):
            verdict_type = audit_verdict.action.type
        else:
            verdict_type = audit_verdict.get("action", {}).get("type")

        if verdict_type in ["ALLOW", "ALLOW_WITH_RESTRICTION"]:
            return True

        logging.warning(f"Governance Verdict ({verdict_type}) blocks execution.")
        return False
