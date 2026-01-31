import logging

from data_bus.schemas import (  # Import necessary Pydantic models
    AuditAction,
    AuditVerdict,
)


class RestrictionEnforcer:
    """
    Applies T2-based restrictions to execution parameters based on audit verdicts.
    """

    def __init__(self, config):
        self.config = config
        self.active_restrictions = {}  # Stores currently active restrictions
        logging.info("Initialized RestrictionEnforcer.")

    def apply_restrictions(self, audit_verdict: AuditVerdict):
        """
        Applies restrictions specified in an audit verdict.
        """
        action = audit_verdict.action
        if action.type == "ALLOW_WITH_RESTRICTION":
            restrictions = action.restrictions if action.restrictions else {}
            logging.warning(f"Applying restrictions: {restrictions}")
            # Merge new restrictions, potentially overriding old ones
            self.active_restrictions.update(restrictions)
        else:
            logging.info("No restrictions to apply from this verdict.")

    def lift_restrictions(self, audit_verdict: AuditVerdict):
        """
        Lifts restrictions specified in an audit verdict, or all if not specified.
        """
        action = audit_verdict.action
        if (
            action.type == "RESTRICTION_LIFTED"
        ):  # Assuming a specific verdict type for lifting
            restrictions_to_lift = (
                action.restrictions.keys() if action.restrictions else []
            )
            for key in restrictions_to_lift:
                if key in self.active_restrictions:
                    del self.active_restrictions[key]
                    logging.info(f"Lifted restriction: {key}")
            if not restrictions_to_lift:  # If no specific restrictions, clear all
                self.active_restrictions.clear()
                logging.info("All restrictions lifted.")
        else:
            logging.info("No restrictions lifted from this verdict.")

    def get_active_restrictions(self) -> dict:
        """
        Returns the currently active restrictions.
        """
        return self.active_restrictions
