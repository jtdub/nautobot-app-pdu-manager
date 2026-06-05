"""Nornir processor for pdu_manager power-control plays."""

from nornir.core.inventory import Host
from nornir.core.task import MultiResult, Task
from nornir_nautobot.plugins.processors import BaseLoggingProcessor


class ProcessPdu(BaseLoggingProcessor):
    """Close host connections and surface unexpected task failures to the JobResult."""

    def __init__(self, logger):
        """Store the NornirLogger used to emit per-device messages."""
        self.logger = logger

    def task_instance_completed(self, task: Task, host: Host, result: MultiResult) -> None:
        """Close connections and log any failure once a host finishes the task."""
        host.close_connections()
        if result.failed:
            # MultiResult is a list of Result; exceptions live on the individual items.
            detail = next((r.exception for r in result if r.exception is not None), None)
            self.logger.error(
                f"`{task.name}` failed: {detail or 'see subtask results'}",
                extra={"object": task.host.data.get("obj")},
            )
