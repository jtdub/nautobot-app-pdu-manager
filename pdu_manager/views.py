"""Views for pdu_manager."""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from nautobot.apps.ui import ObjectDetailContent, ObjectFieldsPanel, SectionChoices
from nautobot.apps.views import NautobotUIViewSet
from nautobot.dcim.models import Device, PowerOutlet
from nautobot.extras.models import Job as JobModel
from nautobot.extras.models import JobResult

from pdu_manager import filters, forms, models, tables
from pdu_manager.api import serializers
from pdu_manager.constants import ACTION_CHOICES
from pdu_manager.utils import connected_outlet_for_device, is_pdu, outlet_index


class PduManagerUIViewSet(NautobotUIViewSet):
    """ViewSet for PduManager views."""

    bulk_update_form_class = forms.PduManagerBulkEditForm
    filterset_class = filters.PduManagerFilterSet
    filterset_form_class = forms.PduManagerFilterForm
    form_class = forms.PduManagerForm
    lookup_field = "pk"
    queryset = models.PduManager.objects.all()
    serializer_class = serializers.PduManagerSerializer
    table_class = tables.PduManagerTable

    # Here is an example of using the UI  Component Framework for the detail view.
    # More information can be found in the Nautobot documentation:
    # https://docs.nautobot.com/projects/core/en/stable/development/core/ui-component-framework/
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields="__all__",
                # Alternatively, you can specify a list of field names:
                # fields=[
                #     "name",
                #     "description",
                # ],
                # Some fields may require additional configuration, we can use value_transforms
                # value_transforms={
                #     "name": [helpers.bettertitle]
                # },
            ),
            # If there is a ForeignKey or M2M with this model we can use ObjectsTablePanel
            # to display them in a table format.
            # ObjectsTablePanel(
            # weight=200,
            # section=SectionChoices.RIGHT_HALF,
            # table_class=tables.PduManagerTable,
            # You will want to filter the table using the related_name
            # filter="pdumanagers",
            # ),
        ],
    )


def _outlet_rows(device):
    """Build the list of outlet rows shown on the control page for ``device``."""
    if is_pdu(device):
        outlets = device.power_outlets.all()
    else:
        connected = connected_outlet_for_device(device)
        outlets = [connected] if connected is not None else []
    return [
        {
            "outlet": outlet,
            "index": outlet_index(outlet),
        }
        for outlet in outlets
    ]


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
        }
        return render(request, "pdu_manager/device_power_control.html", context)


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

        job_model = JobModel.objects.get(
            module_name="pdu_manager.jobs",
            job_class_name="PowerControlJob",
        )
        job_result = JobResult.enqueue_job(
            job_model,
            request.user,
            **job_model.job_class.serialize_data({"device": device, "action": action, "power_outlet": power_outlet}),
        )
        messages.info(request, f"Enqueued PDU '{action}' for {device}.")
        return redirect("extras:jobresult", pk=job_result.pk)
