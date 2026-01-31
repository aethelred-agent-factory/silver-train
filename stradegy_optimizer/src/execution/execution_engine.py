import logging
# from execution.order_manager import OrderManager
# from data_bus.schemas import AuditVerdict, OptimizerProposal

class ExecutionEngine:
    """
    Safe interface to exchange API for trade execution.
    """
    def __init__(self, config, order_manager):
        self.config = config
        self.order_manager = order_manager
        logging.info("Initialized ExecutionEngine.")

    def execute_trade(self, signal: dict, proposal: dict, audit_verdict: dict) -> bool:
        """
        Executes a trade based on a signal, proposal, and audit verdict.
        """
        logging.info(f"Attempting to execute trade with signal: {signal}, proposal ID: {proposal.get('proposal_id')}")

        # 1. Pre-execution safety check based on audit verdict
        if not self.check_execution_safety(proposal, audit_verdict):
            logging.warning("Execution blocked due to safety checks.")
            return False

        # 2. Extract trade details from signal and proposal
        symbol = signal.get('symbol', 'BTC/USDT') # Example
        side = 'buy' if signal.get('signal', 0) == 1 else 'sell' # Example
        amount = signal.get('amount', 0.001) # Example, should be calculated by position manager
        
        # Apply restrictions from audit verdict if any
        if audit_verdict.get('action', {}).get('type') == 'ALLOW_WITH_RESTRICTION':
            restrictions = audit_verdict['action'].get('restrictions', {})
            max_order_size_pct = restrictions.get('max_order_size_pct', 1.0)
            amount = min(amount, amount * max_order_size_pct) # Reduce amount if restricted

        # 3. Place order using OrderManager
        try:
            order_id = self.order_manager.place_order(symbol, side, amount, proposal)
            if order_id:
                logging.info(f"Trade executed: Order ID {order_id} for {side} {amount} {symbol}")
                return True
            else:
                logging.error("Failed to place order.")
                return False
        except Exception as e:
            logging.error(f"Error during order placement: {e}")
            return False

    def check_execution_safety(self, proposal: dict, audit_verdict: dict) -> bool:
        """
        Performs pre-execution checks based on the audit verdict.
        """
        verdict_type = audit_verdict.get('action', {}).get('type')
        
        if verdict_type == 'BLOCK':
            logging.error(f"Execution blocked by audit verdict: {audit_verdict.get('action', {}).get('reason')}")
            return False
        elif verdict_type == 'ALLOW_WITH_RESTRICTION':
            logging.warning("Execution allowed with restrictions.")
            return True # Restrictions will be applied during order placement
        elif verdict_type == 'ALLOW':
            logging.info("Execution allowed by audit verdict.")
            return True
        
        logging.error("Unknown audit verdict type. Blocking execution for safety.")
        return False
