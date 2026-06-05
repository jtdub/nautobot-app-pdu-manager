"""Nornir play that controls APC PDU outlets over SSH.

This mirrors the structure of nautobot-app-golden-config's ``nornir_plays`` (Nautobot ORM
inventory, Secrets-based credentials, a JobResult-aware logger and a processor), but for
the fixed set of APC outlet verbs we call ``netmiko_send_command`` directly with the
``apc_aos`` driver instead of routing through the full nornir-nautobot dispatcher.
"""

import re

from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command

from pdu_manager.constants import (
    ACTION_COMMANDS,
    APC_SUCCESS_CODE,
)
from pdu_manager.nornir_plays.processor import ProcessPdu

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)

# Matches an `olStatus` outlet line, e.g. "    5: Core Switch: On".
_OL_STATUS_RE = re.compile(r"^\s*(?P<id>\d+):\s*(?P<name>.*?):\s*(?P<state>On|Off)\s*$", re.IGNORECASE)


class PduCommandError(Exception):
    """Raised when an APC PDU command does not report success."""


def command_for(action, outlet_ids):
    """Build the APC CLI command string for ``action`` against ``outlet_ids``.

    Args:
        action: One of the on/off/reboot action keys (see ``constants.ACTION_COMMANDS``).
        outlet_ids: Iterable of integer outlet indexes.

    Returns:
        The command string, e.g. ``"olOn 5,6"``.
    """
    verb = ACTION_COMMANDS.get(action)
    if verb is None:
        raise ValueError(f"Unsupported PDU action: {action!r}")
    ids = ",".join(str(int(outlet_id)) for outlet_id in outlet_ids)
    if not ids:
        raise ValueError("At least one outlet id is required.")
    return f"{verb} {ids}"


def check_success(output):
    """Return ``output`` if it reports APC success, else raise ``PduCommandError``."""
    if APC_SUCCESS_CODE not in (output or ""):
        raise PduCommandError(f"APC command did not report {APC_SUCCESS_CODE} success:\n{output}")
    return output


def parse_ol_status(output):
    """Parse ``olStatus all`` output into ``{outlet_id: {"name": str, "state": str}}``."""
    statuses = {}
    for line in (output or "").splitlines():
        match = _OL_STATUS_RE.match(line)
        if match:
            statuses[int(match.group("id"))] = {
                "name": match.group("name").strip(),
                "state": match.group("state").capitalize(),
            }
    return statuses


def _outlet_task(task: Task, command: str) -> Result:
    """Send a single APC CLI ``command`` to the host via netmiko."""
    result = task.run(
        task=netmiko_send_command,
        name=command,
        command_string=command,
        use_timing=True,
    )
    return Result(host=task.host, result=result[0].result)


def _run(pdu, command, logger):
    """Initialize Nornir for a single PDU device and run ``command``, returning raw output."""
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

    Args:
        job: The running Nautobot Job (provides ``job_result`` and ``logger``).
        pdu: The APC PDU ``dcim.Device``.
        action: One of the on/off/reboot action keys.
        outlet_ids: Iterable of integer outlet indexes.

    Returns:
        The raw command output (already verified to contain the success code).
    """
    logger = _logger_for(job)
    command = command_for(action, outlet_ids)
    logger.info(f"Sending `{command}` to {pdu.name}.", extra={"object": pdu})
    output = check_success(_run(pdu, command, logger))
    logger.info(f"`{command}` succeeded on {pdu.name}.", extra={"object": pdu})
    return output


def run_status(job, pdu):
    """Query ``olStatus all`` on ``pdu`` and return ``{outlet_id: {...}}``."""
    logger = _logger_for(job)
    logger.info(f"Querying outlet status on {pdu.name}.", extra={"object": pdu})
    output = _run(pdu, "olStatus all", logger)
    statuses = parse_ol_status(output)
    for outlet_id, info in sorted(statuses.items()):
        logger.info(f"Outlet {outlet_id} ({info['name']}): {info['state']}", extra={"object": pdu})
    return statuses


def _logger_for(job):
    """Return a NornirLogger bound to ``job``'s result and effective log level."""
    from pdu_manager.nornir_plays.logger import NornirLogger  # pylint: disable=import-outside-toplevel

    return NornirLogger(job.job_result, job.logger.getEffectiveLevel())
