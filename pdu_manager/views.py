"""Views for pdu_manager."""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from nautobot.apps.views import NautobotUIViewSet
from nautobot.dcim.models import Device, PowerOutlet
from nautobot.extras.models import Job as JobModel
from nautobot.extras.models import JobResult

from pdu_manager import filters, forms, models, tables
from pdu_manager.api import serializers
from pdu_manager.constants import ACTION_CHOICES
from pdu_manager.utils import (
    blocked_protected_devices,
    connected_outlet_for_device,
    is_pdu,
    is_power_off_protected,
    outlet_index,
)


class PowerOffProtectionUIViewSet(NautobotUIViewSet):
    """Full UI CRUD (list/detail/add/edit/delete/bulk) for PowerOffProtection rules."""

    queryset = models.PowerOffProtection.objects.all()
    table_class = tables.PowerOffProtectionTable
    form_class = forms.PowerOffProtectionForm
    filterset_class = filters.PowerOffProtectionFilterSet
    filterset_form_class = forms.PowerOffProtectionFilterForm
    bulk_update_form_class = forms.PowerOffProtectionBulkEditForm
    serializer_class = serializers.PowerOffProtectionSerializer


class PduCommandSetUIViewSet(NautobotUIViewSet):
    """Full UI CRUD (list/detail/add/edit/delete/bulk) for PDU Command Sets."""

    queryset = models.PduCommandSet.objects.all()
    table_class = tables.PduCommandSetTable
    form_class = forms.PduCommandSetForm
    filterset_class = filters.PduCommandSetFilterSet
    filterset_form_class = forms.PduCommandSetFilterForm
    bulk_update_form_class = forms.PduCommandSetBulkEditForm
    serializer_class = serializers.PduCommandSetSerializer


class PduOutletStatusUIViewSet(NautobotUIViewSet):
    """UI CRUD (list/detail/delete/bulk) for stored PDU outlet statuses.

    Rows are normally populated by a Status run rather than created by hand, but the list and
    detail views make the stored state browsable and the rows deletable.
    """

    queryset = models.PduOutletStatus.objects.select_related("device", "power_outlet")
    table_class = tables.PduOutletStatusTable
    form_class = forms.PduOutletStatusForm
    filterset_class = filters.PduOutletStatusFilterSet
    filterset_form_class = forms.PduOutletStatusFilterForm
    bulk_update_form_class = forms.PduOutletStatusBulkEditForm
    serializer_class = serializers.PduOutletStatusSerializer


def _outlet_rows(device):
    """Build the list of outlet rows shown on the control page for ``device``.

    Each row carries a ``protected`` flag: True when the action would remove power from a
    device covered by a PowerOffProtection rule (the invoked device, or a device fed by
    the outlet when controlling a PDU). The template uses it to disable Off/Reboot.
    """
    if is_pdu(device):
        outlets = device.power_outlets.all()
    else:
        connected = connected_outlet_for_device(device)
        outlets = [connected] if connected is not None else []
    rows = []
    for outlet in outlets:
        # ACTION_OFF is a protected action, so this reflects the Off/Reboot block.
        protected = bool(blocked_protected_devices(device, "off", [outlet]))
        rows.append({"outlet": outlet, "index": outlet_index(outlet), "protected": protected})
    return rows


class DevicePowerControlView(PermissionRequiredMixin, View):
    """Render the PDU power-control page for a device (PDU or PDU-powered device)."""

    permission_required = "extras.run_job"

    def get(self, request, pk):
        """Display each controllable outlet with on/off/reboot/status actions."""
        device = get_object_or_404(Device.objects.restrict(request.user, "view"), pk=pk)
        context = {
            "device": device,
            "is_pdu": is_pdu(device),
            "outlet_rows": _outlet_rows(device),
            "actions": ACTION_CHOICES,
            "device_protected": is_power_off_protected(device),
        }
        return render(request, "pdu_manager/device_power_control.html", context)


def _enqueue_power_action(request, device, action, power_outlet, target_label):
    """Protection-check and enqueue PowerControlJob for ``device``/``action``/``power_outlet``.

    Returns ``(job_result, None)`` on success, or ``(None, error_message)`` when a Power Off
    Protection rule blocks the action. The single place both power-action views share.
    """
    protected = blocked_protected_devices(device, action, [power_outlet] if power_outlet else [])
    if protected:
        names = ", ".join(sorted(dev.name for dev in protected))
        return None, f"Refusing to '{action}' {target_label}: blocked by a Power Off Protection rule matching {names}."

    job_model = JobModel.objects.get(module_name="pdu_manager.jobs", job_class_name="PowerControlJob")
    job_result = JobResult.enqueue_job(
        job_model,
        request.user,
        **job_model.job_class.serialize_data({"device": device, "action": action, "power_outlet": power_outlet}),
    )
    return job_result, None


class DevicePowerActionView(PermissionRequiredMixin, View):
    """Enqueue the PowerControlJob for a requested device/outlet/action and redirect."""

    permission_required = "extras.run_job"

    def post(self, request, pk):
        """Validate input, enqueue PowerControlJob, and redirect to its JobResult."""
        device = get_object_or_404(Device.objects.restrict(request.user, "view"), pk=pk)
        action = request.POST.get("action")
        outlet_pk = request.POST.get("power_outlet") or None

        valid_actions = {key for key, _ in ACTION_CHOICES}
        if action not in valid_actions:
            messages.error(request, f"Invalid power action: {action!r}.")
            return redirect("plugins:pdu_manager:device_power_control", pk=pk)

        power_outlet = None
        if outlet_pk:
            power_outlet = get_object_or_404(PowerOutlet.objects.restrict(request.user, "view"), pk=outlet_pk)

        job_result, error = _enqueue_power_action(request, device, action, power_outlet, device.name)
        if error:
            messages.error(request, error)
            return redirect("plugins:pdu_manager:device_power_control", pk=pk)

        messages.info(request, f"Enqueued PDU '{action}' for {device}.")
        return redirect("extras:jobresult", pk=job_result.pk)


class OutletPowerActionView(PermissionRequiredMixin, View):
    """Enqueue a power action for a single stored outlet (the status table's row buttons)."""

    permission_required = "extras.run_job"

    def get(self, request, pk, action):
        """Validate the action, enforce protection, enqueue PowerControlJob, and redirect."""
        status = get_object_or_404(
            models.PduOutletStatus.objects.select_related("device", "power_outlet").restrict(request.user, "view"),
            pk=pk,
        )
        device = status.device
        power_outlet = status.power_outlet

        valid_actions = {key for key, _ in ACTION_CHOICES}
        if action not in valid_actions:
            messages.error(request, f"Invalid power action: {action!r}.")
            return redirect(device.get_absolute_url())

        job_result, error = _enqueue_power_action(request, device, action, power_outlet, str(power_outlet))
        if error:
            messages.error(request, error)
            return redirect(device.get_absolute_url())

        messages.info(request, f"Enqueued PDU '{action}' for {power_outlet}.")
        return redirect("extras:jobresult", pk=job_result.pk)
