import logging
from datetime import datetime, timedelta, timezone


class TimeUtils:
    """
    Utility functions for timezone-aware datetime handling.
    """

    def __init__(self):
        logging.info("Initialized TimeUtils.")

    def now_utc(self) -> datetime:
        """
        Returns the current UTC datetime with timezone information.
        """
        return datetime.now(timezone.utc)

    def parse_iso8601(self, iso_string: str) -> datetime:
        """
        Parses an ISO 8601 formatted string to a timezone-aware datetime object.
        """
        try:
            # Python's datetime.fromisoformat handles various ISO 8601 formats
            dt = datetime.fromisoformat(iso_string)
            if dt.tzinfo is None:
                # Assume UTC if no timezone info is provided
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError as e:
            logging.error(f"Failed to parse ISO 8601 string '{iso_string}': {e}")
            raise

    def to_iso8601(self, dt_object: datetime) -> str:
        """
        Converts a datetime object to an ISO 8601 formatted string (with 'Z' for UTC).
        Ensures the datetime object is timezone-aware.
        """
        if dt_object.tzinfo is None:
            # Assume UTC if no timezone info, then convert to ISO with 'Z'
            return (
                dt_object.replace(tzinfo=timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
        return dt_object.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def ensure_causal(self, timestamp: datetime, reference_timestamp: datetime) -> bool:
        """
        Ensures that a given timestamp is not in the future relative to a reference timestamp.
        Returns True if causal, False otherwise.
        """
        if timestamp > reference_timestamp:
            logging.error(
                f"Causality violation: Timestamp ({timestamp}) is after reference ({reference_timestamp})."
            )
            return False
        return True
