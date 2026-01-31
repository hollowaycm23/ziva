import logging
import json
from typing import Dict, Any

logger = logging.getLogger("Auditor")


class Auditor:
    """
    Centralized auditor for LangGraph events and critical system actions.
    Provides structured logging for observability.
    """

    @staticmethod
    def log_event(event_type: str, data: Dict[str, Any], level: str = "INFO"):
        """
        Logs a structured event.

        Args:
            event_type (str): Category of the event (e.g., NODE_START,
                              TOOL_EXECUTION).
            data (dict): key-value pairs of event data.
            level (str): Log level (INFO, WARNING, ERROR, DEBUG).
        """
        try:
            # simple serialization to string for logging
            msg = f"[{event_type}] {json.dumps(data, default=str)}"

            if level.upper() == "INFO":
                logger.info(msg)
            elif level.upper() == "WARNING":
                logger.warning(msg)
            elif level.upper() == "ERROR":
                logger.error(msg)
            elif level.upper() == "DEBUG":
                logger.debug(msg)
            else:
                logger.info(msg)

        except Exception as e:
            # Fallback if JSON fails
            logger.error(f"Failed to log event {event_type}: {e}")
