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
from pdu_manager.utils import (
    blocked_protected_devices,
    record_outlet_action_result,
    record_outlet_statuses,
    resolve_pdu_and_outlets,
)

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
            # The action succeeded (run_power_action raises otherwise); reflect the new state.
            record_outlet_action_result(pdu, outlet_ids, action)
            self.logger.info("'%s' completed on %s outlet(s) %s.", action, pdu.name, outlet_ids)
            return f"{action} completed on {pdu.name} outlet(s) {outlet_ids}."
        except (ValueError, power_control.PduCommandError) as error:
            return self._fail(str(error))

    def _run_status(self, device, power_outlet):
        """Report outlet status scoped to the device acted on (not the whole PDU).

        A specific outlet (or a downstream device's feeding outlet) queries just that
        outlet; the Status action on a PDU itself reports all of its outlets. The parsed
        statuses are persisted to the ``PduOutletStatus`` model so the device-page panel
        reflects the latest poll.
        """
        if power_outlet is not None:
            pdu, outlet_ids = resolve_pdu_and_outlets(device, power_outlet)
            statuses = power_control.run_status(self, pdu, outlet_ids)
        elif device.power_outlets.exists():
            pdu = device
            statuses = power_control.run_status(self, pdu)
        else:
            pdu, outlet_ids = resolve_pdu_and_outlets(device)
            statuses = power_control.run_status(self, pdu, outlet_ids)
        record_outlet_statuses(pdu, statuses)
        return statuses

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
    """Read and store PDU outlet status.

    With a ``device`` it reads status scoped to that device (the device-page button) and
    updates the stored ``PduOutletStatus`` rows. Left blank — as for a scheduled run — it
    polls **every** PDU and refreshes all of their stored outlet states.
    """

    power_action = ACTION_STATUS

    # Override the shared (required) device input: blank means "every PDU" for scheduled runs.
    device = ObjectVar(
        model=Device,
        required=False,
        description="A PDU, or a device powered by a PDU outlet. Leave blank to refresh every PDU.",
    )

    class Meta:  # pylint: disable=too-few-public-methods
        """Job metadata."""

        name = "PDU Power: Status"
        description = "Read and store APC PDU outlet status (a device, or every PDU when left blank)."
        has_sensitive_variables = False

    def run(self, device=None, power_outlet=None):  # pylint: disable=arguments-differ
        """Refresh status for ``device`` (and optional ``power_outlet``), or every PDU."""
        if device is not None:
            return self._execute(device, self.power_action, power_outlet)
        return self._sync_all_pdus()

    def _sync_all_pdus(self):
        """Poll and store outlet status for every PDU; per-PDU errors are logged, not fatal."""
        pdus = Device.objects.filter(power_outlets__isnull=False).prefetch_related("power_outlets").distinct()
        total = synced = 0
        for pdu in pdus:
            total += 1
            try:
                self._run_status(pdu, None)
                synced += 1
            except (ValueError, power_control.PduCommandError) as error:
                self.logger.warning("Skipped PDU %s: %s", pdu.name, error)
        message = f"Refreshed outlet status for {synced}/{total} PDU(s)."
        self.logger.info(message)
        return message


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
