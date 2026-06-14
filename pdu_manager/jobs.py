"""Jobs for pdu_manager.

``PowerControlJob`` is the full-form job (device + outlet + action choice) used by the
power-control page. The per-action jobs (``PowerStatusJob``/``PowerOnJob``/``PowerOffJob``/
``PowerRebootJob``) back the built-in device-page dropdown (one job per menu item); they all
share the resolve/protection/delegate logic in ``_BasePduJob``.
"""

from nautobot.apps.jobs import ChoiceVar, Job, ObjectVar, register_jobs
from nautobot.dcim.models import Device, PowerOutlet

from pdu_manager.constants import ACTION_CHOICES, ACTION_OFF, ACTION_ON, ACTION_REBOOT, ACTION_STATUS
from pdu_manager.nornir_plays import power_control
from pdu_manager.utils import blocked_protected_devices, resolve_pdu_and_outlets

# `name` (lowercase) is the Nautobot-required module attribute for Job grouping.
name = "PDU Manager"  # pylint: disable=invalid-name


class _BasePduJob(Job):  # pylint: disable=abstract-method
    """Shared device/outlet inputs and resolve/protection/delegate logic for PDU jobs.

    Abstract base: not registered and intentionally does not implement ``run()`` (the
    concrete subclasses do).
    """

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

    def _execute(self, device, action, power_outlet=None):
        """Guard protection, resolve the target outlet(s), and delegate to the Nornir play.

        Expected problems (a protected device, no PDU outlet, an outlet whose name has no
        number) are reported as a clean Job **Failure** log entry via ``self.fail()`` rather
        than an unhandled traceback.
        """
        protected = blocked_protected_devices(device, action, [power_outlet] if power_outlet else [])
        if protected:
            names = ", ".join(sorted(dev.name for dev in protected))
            return self._fail(
                f"Refusing to '{action}' {device.name}: blocked by a Power Off Protection rule matching {names}."
            )

        try:
            if action == ACTION_STATUS:
                return self._run_status(device, power_outlet)

            pdu, outlet_ids = resolve_pdu_and_outlets(device, power_outlet)
            self.logger.info("Resolved %s action to PDU %s outlet(s) %s.", action, pdu.name, outlet_ids)
            power_control.run_power_action(self, pdu, action, outlet_ids)
            self.logger.info("'%s' completed on %s outlet(s) %s.", action, pdu.name, outlet_ids)
            return f"{action} completed on {pdu.name} outlet(s) {outlet_ids}."
        except (ValueError, power_control.PduCommandError) as error:
            return self._fail(str(error))

    def _run_status(self, device, power_outlet):
        """Report outlet status scoped to the device acted on (not the whole PDU).

        A specific outlet (or a downstream device's feeding outlet) queries just that
        outlet; the Status action on a PDU itself reports all of its outlets.
        """
        if power_outlet is not None:
            pdu, outlet_ids = resolve_pdu_and_outlets(device, power_outlet)
            return power_control.run_status(self, pdu, outlet_ids)
        if device.power_outlets.exists():
            return power_control.run_status(self, device)
        pdu, outlet_ids = resolve_pdu_and_outlets(device)
        return power_control.run_status(self, pdu, outlet_ids)

    def _fail(self, message):
        """Log ``message`` as a Job Failure entry, mark the job failed, and echo it back."""
        self.fail(message)
        return message


class PowerControlJob(_BasePduJob):
    """Power an APC PDU outlet on/off, reboot it, or read outlet status over SSH."""

    action = ChoiceVar(choices=ACTION_CHOICES)

    class Meta:  # pylint: disable=too-few-public-methods
        """Job metadata."""

        name = "PDU Power Control"
        description = "Control APC PDU outlets (on/off/reboot) and read outlet status."
        has_sensitive_variables = False

    def run(self, device, action, power_outlet=None):  # pylint: disable=arguments-differ
        """Resolve the target PDU/outlet and delegate to the Nornir play."""
        return self._execute(device, action, power_outlet)


class _SingleActionJob(_BasePduJob):
    """Base for the per-action dropdown jobs; ``power_action`` is set by each subclass."""

    power_action = None

    def run(self, device, power_outlet=None):  # pylint: disable=arguments-differ
        """Run this job's fixed action against ``device`` (and optional ``power_outlet``)."""
        return self._execute(device, self.power_action, power_outlet)


class PowerStatusJob(_SingleActionJob):
    """Read PDU outlet status for a device (scoped to its outlet, or all for a PDU)."""

    power_action = ACTION_STATUS

    class Meta:  # pylint: disable=too-few-public-methods
        """Job metadata."""

        name = "PDU Power: Status"
        description = "Read APC PDU outlet status for the selected device."
        has_sensitive_variables = False


class PowerOnJob(_SingleActionJob):
    """Power ON the PDU outlet(s) feeding a device."""

    power_action = ACTION_ON

    class Meta:  # pylint: disable=too-few-public-methods
        """Job metadata."""

        name = "PDU Power: On"
        description = "Power ON the APC PDU outlet(s) feeding the selected device."
        has_sensitive_variables = False


class PowerOffJob(_SingleActionJob):
    """Power OFF the PDU outlet(s) feeding a device (refused for protected devices)."""

    power_action = ACTION_OFF

    class Meta:  # pylint: disable=too-few-public-methods
        """Job metadata."""

        name = "PDU Power: Off"
        description = "Power OFF the APC PDU outlet(s) feeding the selected device."
        has_sensitive_variables = False


class PowerRebootJob(_SingleActionJob):
    """Reboot the PDU outlet(s) feeding a device (refused for protected devices)."""

    power_action = ACTION_REBOOT

    class Meta:  # pylint: disable=too-few-public-methods
        """Job metadata."""

        name = "PDU Power: Reboot"
        description = "Reboot the APC PDU outlet(s) feeding the selected device."
        has_sensitive_variables = False


register_jobs(PowerControlJob, PowerStatusJob, PowerOnJob, PowerOffJob, PowerRebootJob)
