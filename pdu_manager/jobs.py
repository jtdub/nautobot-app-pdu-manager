"""Jobs for pdu_manager."""

from nautobot.apps.jobs import ChoiceVar, Job, ObjectVar, register_jobs
from nautobot.dcim.models import Device, PowerOutlet

from pdu_manager.constants import ACTION_CHOICES, ACTION_STATUS
from pdu_manager.nornir_plays import power_control
from pdu_manager.utils import resolve_pdu_and_outlets

# `name` (lowercase) is the Nautobot-required module attribute for Job grouping.
name = "PDU Manager"  # pylint: disable=invalid-name


class PowerControlJob(Job):
    """Power an APC PDU outlet on/off, reboot it, or read outlet status over SSH."""

    device = ObjectVar(
        model=Device,
        description="The PDU itself, or a device powered by a PDU outlet.",
    )
    power_outlet = ObjectVar(
        model=PowerOutlet,
        required=False,
        label="Outlet",
        description="Required when running against a PDU with more than one outlet. "
        "Leave blank for a device powered by a single outlet.",
        query_params={"device_id": "$device"},
    )
    action = ChoiceVar(choices=ACTION_CHOICES)

    class Meta:  # pylint: disable=too-few-public-methods
        """Job metadata."""

        name = "PDU Power Control"
        description = "Control APC PDU outlets (on/off/reboot) and read outlet status."
        has_sensitive_variables = False

    def run(self, device, action, power_outlet=None):  # pylint: disable=arguments-differ
        """Resolve the target PDU/outlet and delegate to the Nornir play."""
        if action == ACTION_STATUS:
            pdu = device if device.power_outlets.exists() else None
            if pdu is None:
                # Downstream device: resolve its feeding PDU to query the whole unit.
                pdu_device, _ = resolve_pdu_and_outlets(device, power_outlet)
                pdu = pdu_device
            return power_control.run_status(self, pdu)

        pdu, outlet_ids = resolve_pdu_and_outlets(device, power_outlet)
        self.logger.info(
            "Resolved %s action to PDU %s outlet(s) %s.",
            action,
            pdu.name,
            outlet_ids,
        )
        power_control.run_power_action(self, pdu, action, outlet_ids)
        return f"{action} completed on {pdu.name} outlet(s) {outlet_ids}."


register_jobs(PowerControlJob)
