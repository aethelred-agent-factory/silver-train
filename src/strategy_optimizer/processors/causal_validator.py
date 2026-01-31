import logging
from datetime import datetime

import pandas as pd


class CausalValidator:
    """
    Ensures that all computations are timestamp-causal.
    """

    def __init__(self):
        logging.info("Initialized CausalValidator.")

    def validate_timestamp_causality(
        self, computation_timestamp: datetime, data: pd.DataFrame
    ) -> bool:
        """
        Validates that all data used for a computation has a timestamp
        less than or equal to the computation's timestamp.

        Args:
            computation_timestamp: The timestamp of the computation (e.g., proposal).
            data: The DataFrame used for the computation.

        Returns:
            True if causal, False otherwise.
        """
        if data.empty:
            return True  # No data to violate causality

        # Ensure data timestamps are not in the future
        max_data_timestamp = data["timestamp"].max()
        if max_data_timestamp > computation_timestamp:
            logging.error(
                f"Causality violation! Data timestamp ({max_data_timestamp}) "
                f"is after computation timestamp ({computation_timestamp})."
            )
            return False

        return True

    def validate_causal_chain(self, chain: list, proposal_timestamp: datetime):
        """
        Validates the entire causal chain of a proposal.
        (Placeholder for now, will be more complex in a real system)

        Args:
            chain: A list of causal chain references.
            proposal_timestamp: The timestamp of the proposal.

        """
        # TODO: This is a simplified check. A full implementation would involve:
        # - Retrieving each artifact in the chain from the artifact store.
        # - Checking the timestamp of each artifact.
        # - Ensuring all artifacts were created before the proposal.
        logging.info(f"Validating causal chain for proposal at {proposal_timestamp}.")
        # In this placeholder, we assume the chain is a list of dataframes or objects with a timestamp
        for link in chain:
            if hasattr(link, "timestamp") and link.timestamp > proposal_timestamp:
                logging.error(
                    f"Causal chain violation: item in chain is from the future."
                )
                return False
        return True
