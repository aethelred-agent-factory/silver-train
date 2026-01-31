
import logging
from storage.state_manager import StateManager

class KillSwitch:
    """
    Manages the global kill switch for the trading system.
    """

    def __init__(self, state_manager: StateManager):
        """
        Initializes the KillSwitch with a StateManager instance.

        Args:
            state_manager (StateManager): The state manager to persist the kill switch state.
        """
        self._state_manager = state_manager

    def activate(self):
        """
        Activates the global kill switch.
        """
        logging.critical("ACTIVATING GLOBAL KILL SWITCH")
        self._state_manager.save_state('GLOBAL_KILL_SWITCH', 'HALTED')

    def deactivate(self):
        """
        Deactivates the global kill switch.
        """
        logging.warning("Deactivating global kill switch.")
        self._state_manager.save_state('GLOBAL_KILL_SWITCH', 'OPERATIONAL')

    def is_active(self) -> bool:
        """
        Checks if the kill switch is active.

        Returns:
            bool: True if the kill switch is active, False otherwise.
        """
        return self._state_manager.is_kill_switch_active()
