"""Nornir play that controls managed PDU outlets over SSH.

This mirrors the structure of nautobot-app-golden-config's ``nornir_plays`` (Nautobot ORM
inventory, Secrets-based credentials, a JobResult-aware logger and a processor), but for
the fixed set of outlet verbs we call ``netmiko_send_command`` directly with the device's
platform ``network_driver`` instead of routing through the full nornir-nautobot dispatcher.

The actual commands, success marker, and status-parsing regex are **not** hard-coded: they
come from the :class:`~pdu_manager.models.PduCommandSet` assigned to the PDU's Platform,
resolved at run time by ``utils.command_set_for``.
"""

from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command

from pdu_manager.config import mock_connections_enabled
from pdu_manager.nornir_plays.mock import simulate_command
from pdu_manager.nornir_plays.processor import ProcessPdu
from pdu_manager.utils import command_set_for

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)


class PduCommandError(Exception):
    """Raised when a PDU command does not report success."""


def _outlet_task(task: Task, command: str) -> Result:
    """Send a single CLI ``command`` to the host via netmiko."""
    result = task.run(
        task=netmiko_send_command,
        name=command,
        command_string=command,
        use_timing=True,
    )
    return Result(host=task.host, result=result[0].result)


def _run(pdu, command, logger, command_set):
    """Initialize Nornir for a single PDU device and run ``command``, returning raw output."""
    if mock_connections_enabled():
        logger.info(
            f"[MOCK_CONNECTIONS] Simulating `{command}` on {pdu.name}; no SSH session opened.",
            extra={"object": pdu},
        )
        return simulate_command(pdu, command, command_set)

    # Import here to avoid importing the Django ORM at module load time.
    from nautobot.dcim.models import Device  # pylint: disable=import-outside-toplevel

    with InitNornir(
        runner=NORNIR_SETTINGS.get("runner"),
        logging={"enabled": False},
        inventory={
            "plugin": "nautobot-inventory",
            "options": {
                "credentials_class": NORNIR_SETTINGS.get("credentials"),
                "params": NORNIR_SETTINGS.get("inventory_params"),
                "queryset": Device.objects.filter(pk=pdu.pk),
            },
        },
    ) as nornir_obj:
        agg_result = nornir_obj.with_processors([ProcessPdu(logger)]).run(
            task=_outlet_task,
            command=command,
        )
    # AggregatedResult[host] is a MultiResult (list of Result); item [0] is _outlet_task's
    # own Result, whose .result holds the netmiko command output.
    host_result = agg_result[pdu.name]
    if host_result.failed:
        detail = next((r.exception for r in host_result if r.exception is not None), None)
        raise PduCommandError(f"PDU command `{command}` failed on {pdu.name}: {detail}")
    return host_result[0].result


def run_power_action(job, pdu, action, outlet_ids):
    """Execute an on/off/reboot ``action`` against ``outlet_ids`` on ``pdu``.

    The command and success check come from the PDU Platform's ``PduCommandSet``.

    Returns:
        The raw command output (already verified against the command set's success string).
    """
    logger = _logger_for(job)
    command_set = command_set_for(pdu)
    command = command_set.build_command(action, outlet_ids)
    logger.info(f"Sending `{command}` to {pdu.name}.", extra={"object": pdu})
    output = _run(pdu, command, logger, command_set)
    if not command_set.check_success(output):
        raise PduCommandError(
            f"`{command}` on {pdu.name} did not report success ('{command_set.success_string}'):\n{output}"
        )
    logger.info(f"`{command}` succeeded on {pdu.name}.", extra={"object": pdu})
    return output


def run_status(job, pdu, outlet_ids=None):
    """Query outlet status on ``pdu`` and return ``{outlet_id: {...}}``.

    With ``outlet_ids`` the query is scoped to those outlets; otherwise the whole unit is
    queried. Scoping keeps a single-device Status from reporting every outlet on the PDU.
    The status command and parsing regex come from the PDU Platform's ``PduCommandSet``.
    """
    logger = _logger_for(job)
    command_set = command_set_for(pdu)
    command = command_set.build_status_command(outlet_ids)
    scope = "all outlets" if not outlet_ids else f"outlet(s) {','.join(str(outlet_id) for outlet_id in outlet_ids)}"
    logger.info(f"Querying {scope} status on {pdu.name}.", extra={"object": pdu})
    output = _run(pdu, command, logger, command_set)
    statuses = command_set.parse_status(output)
    for outlet_id, info in sorted(statuses.items()):
        logger.info(f"Outlet {outlet_id} ({info['name']}): {info['state']}", extra={"object": pdu})
    return statuses


def _logger_for(job):
    """Return a NornirLogger bound to ``job``'s result and effective log level."""
    from pdu_manager.nornir_plays.logger import NornirLogger  # pylint: disable=import-outside-toplevel

    return NornirLogger(job.job_result, job.logger.getEffectiveLevel())
