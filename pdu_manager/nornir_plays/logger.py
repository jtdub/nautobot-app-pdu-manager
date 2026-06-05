"""Thread-safe logger that mirrors Nornir task output to a Nautobot JobResult.

Mirrors the pattern used by nautobot-app-golden-config so per-device log lines attach to
the relevant object in the Job results UI via ``extra={"object": device}``.
"""

import logging

LOGGER = logging.getLogger(__name__)


class NornirLogger:
    """Logger that writes both to the stdlib logger and the Nautobot JobResult."""

    def __init__(self, job_result, log_level):
        """Store the JobResult and configure the stdlib log level."""
        self.job_result = job_result
        LOGGER.setLevel(log_level)

    def _logging_helper(self, attr, message, extra=None):
        extra = extra or {}
        getattr(LOGGER, attr)(message)
        self.job_result.log(
            message,
            level_choice=attr,
            obj=extra.get("object"),
            grouping=extra.get("grouping", ""),
        )

    def debug(self, message, extra=None):
        """Log a debug message."""
        self._logging_helper("debug", message, extra)

    def info(self, message, extra=None):
        """Log an info message."""
        self._logging_helper("info", message, extra)

    def warning(self, message, extra=None):
        """Log a warning message."""
        self._logging_helper("warning", message, extra)

    def error(self, message, extra=None):
        """Log an error message."""
        self._logging_helper("error", message, extra)

    def critical(self, message, extra=None):
        """Log a critical message."""
        self._logging_helper("critical", message, extra)
