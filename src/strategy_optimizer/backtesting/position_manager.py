import logging


class PositionManager:
    """
    Handles position sizing and stop-loss/take-profit placement.
    """

    def __init__(self, config):
        self.config = config
        self.parameter_bounds = config["parameter_bounds"]
        logging.info("Initialized PositionManager.")

    def calculate_position_size(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        Calculates the position size based on the risk percentage of the capital.
        """
        if entry_price <= stop_loss_price:
            logging.warning(
                "Stop loss price must be below entry price for a long position."
            )
            return 0

        risk_per_share = entry_price - stop_loss_price
        risk_amount = capital * (risk_pct / 100)

        position_size = risk_amount / risk_per_share

        # In a real system, you would also consider the total available capital
        # and not allow the position size to exceed it.
        # For simplicity, we assume we have enough capital.

        return position_size

    def place_stop_loss(
        self, entry_price: float, atr: float, multiplier: float
    ) -> float:
        """
        Calculates the stop-loss price using an ATR multiplier.
        """
        stop_loss_price = entry_price - (atr * multiplier)
        return stop_loss_price

    def place_take_profit(
        self, entry_price: float, atr: float, multiplier: float
    ) -> float:
        """
        Calculates the take-profit price using an ATR multiplier.
        """
        take_profit_price = entry_price + (atr * multiplier)
        return take_profit_price
