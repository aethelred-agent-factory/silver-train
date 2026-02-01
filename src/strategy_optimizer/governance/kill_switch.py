import logging

from storage.interface import StorageInterface

KILL_SWITCH_KEY = "GLOBAL_KILL_SWITCH"

class KillSwitch:
    """
    Manages the global kill switch for the trading system.
    """

    def __init__(self, storage: StorageInterface):
        """
        Initializes the KillSwitch with a StorageInterface instance.

        Args:
            storage (StorageInterface): The storage to persist the kill switch state.
        """
        self._storage = storage

    def activate(self):
        """
        Activates the global kill switch.
        """
        logging.critical("ACTIVATING GLOBAL KILL SWITCH")
        self._storage.save_state(KILL_SWITCH_KEY, {"status": "HALTED"})

    def deactivate(self):
        """
        Deactivates the global kill switch.
        """
        logging.warning("Deactivating global kill switch.")
        self._storage.save_state(KILL_SWITCH_KEY, {"status": "OPERATIONAL"})

    def is_active(self) -> bool:
        """
        Checks if the kill switch is active.

        Returns:
            bool: True if the kill switch is active, False otherwise.
        """
        state = self._storage.load_state(KILL_SWITCH_KEY)
        return state is not None and state.get("status") == "HALTED"
