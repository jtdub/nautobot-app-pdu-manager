"""Forms for pdu_manager."""

from django import forms
from nautobot.apps.constants import CHARFIELD_MAX_LENGTH
from nautobot.apps.forms import (
    DynamicModelMultipleChoiceField,
    NautobotBulkEditForm,
    NautobotFilterForm,
    NautobotModelForm,
    StaticSelect2,
    StaticSelect2Multiple,
    TagsBulkEditFormMixin,
)
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import Role, Tag
from nautobot.tenancy.models import Tenant

from pdu_manager import models


class PowerOffProtectionForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """Create/edit form for a PowerOffProtection rule."""

    roles = DynamicModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False,
        query_params={"content_types": "dcim.device"},
    )
    tenants = DynamicModelMultipleChoiceField(queryset=Tenant.objects.all(), required=False)
    device_tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        query_params={"content_types": "dcim.device"},
        label="Device tags",
    )
    devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False)

    class Meta:
        """Meta attributes."""

        model = models.PowerOffProtection
        fields = "__all__"


class PowerOffProtectionBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """Bulk-edit form for PowerOffProtection rules."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.PowerOffProtection.objects.all(), widget=forms.MultipleHiddenInput
    )
    enabled = forms.NullBooleanField(
        required=False, widget=StaticSelect2(choices=(("", "---------"), (True, "Yes"), (False, "No")))
    )
    description = forms.CharField(required=False, max_length=CHARFIELD_MAX_LENGTH)

    class Meta:
        """Meta attributes."""

        nullable_fields = ["description"]


class PowerOffProtectionFilterForm(NautobotFilterForm):  # pylint: disable=too-many-ancestors
    """Filter form for the PowerOffProtection list view."""

    model = models.PowerOffProtection
    field_order = ["q", "name", "enabled", "roles", "tenants", "device_tags", "devices"]

    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Name")
    enabled = forms.NullBooleanField(
        required=False, widget=StaticSelect2(choices=(("", "---------"), (True, "Yes"), (False, "No")))
    )
    roles = DynamicModelMultipleChoiceField(queryset=Role.objects.all(), required=False)
    tenants = DynamicModelMultipleChoiceField(queryset=Tenant.objects.all(), required=False)
    device_tags = DynamicModelMultipleChoiceField(queryset=Tag.objects.all(), required=False, label="Device tags")
    devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False)


class PduCommandSetForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """Create/edit form for a PDU Command Set."""

    platforms = DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)

    class Meta:
        """Meta attributes."""

        model = models.PduCommandSet
        fields = "__all__"


class PduCommandSetBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """Bulk-edit form for PDU Command Sets."""

    pk = forms.ModelMultipleChoiceField(queryset=models.PduCommandSet.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False, max_length=CHARFIELD_MAX_LENGTH)
    success_string = forms.CharField(required=False, max_length=CHARFIELD_MAX_LENGTH)

    class Meta:
        """Meta attributes."""

        nullable_fields = ["description"]


class PduCommandSetFilterForm(NautobotFilterForm):  # pylint: disable=too-many-ancestors
    """Filter form for the PDU Command Set list view."""

    model = models.PduCommandSet
    field_order = ["q", "name", "platforms"]

    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Name")
    platforms = DynamicModelMultipleChoiceField(queryset=Platform.objects.all(), required=False)


class PduOutletStatusForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """Create/edit form for a stored PDU outlet status (normally job-managed)."""

    class Meta:
        """Meta attributes."""

        model = models.PduOutletStatus
        fields = "__all__"


class PduOutletStatusBulkEditForm(NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """Bulk-edit form for stored PDU outlet statuses (e.g. mark a selection On/Off)."""

    pk = forms.ModelMultipleChoiceField(queryset=models.PduOutletStatus.objects.all(), widget=forms.MultipleHiddenInput)
    state = forms.ChoiceField(
        choices=[("", "---------"), *models.PduOutletStatus._meta.get_field("state").choices],
        required=False,
        widget=StaticSelect2,
    )

    class Meta:
        """Meta attributes."""

        nullable_fields = []


class PduOutletStatusFilterForm(NautobotFilterForm):  # pylint: disable=too-many-ancestors
    """Filter form for the PDU Outlet Status list view."""

    model = models.PduOutletStatus
    field_order = ["q", "device", "state"]

    q = forms.CharField(required=False, label="Search")
    device = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), required=False)
    state = forms.MultipleChoiceField(
        choices=models.PduOutletStatus._meta.get_field("state").choices,
        required=False,
        widget=StaticSelect2Multiple,
    )
