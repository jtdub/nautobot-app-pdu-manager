"""Filtering for pdu_manager."""

import django_filters
from nautobot.apps.filters import NaturalKeyOrPKMultipleChoiceFilter, NautobotFilterSet, SearchFilter
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import Role, Tag
from nautobot.tenancy.models import Tenant

from pdu_manager import models


class PowerOffProtectionFilterSet(NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for PowerOffProtection."""

    q = SearchFilter(filter_predicates={"name": "icontains", "description": "icontains"})
    roles = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Role.objects.all(),
        to_field_name="name",
        label="Role (name or ID)",
    )
    tenants = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        to_field_name="name",
        label="Tenant (name or ID)",
    )
    device_tags = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        to_field_name="name",
        label="Device tag (name or ID)",
    )
    devices = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Device.objects.all(),
        to_field_name="name",
        label="Device (name or ID)",
    )
    enabled = django_filters.BooleanFilter()

    class Meta:
        """Meta attributes for filter."""

        model = models.PowerOffProtection
        fields = "__all__"


class PduCommandSetFilterSet(NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for PduCommandSet."""

    q = SearchFilter(filter_predicates={"name": "icontains", "description": "icontains"})
    platforms = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (name or ID)",
    )

    class Meta:
        """Meta attributes for filter."""

        model = models.PduCommandSet
        fields = "__all__"


class PduOutletStatusFilterSet(NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for PduOutletStatus."""

    q = SearchFilter(filter_predicates={"device__name": "icontains", "power_outlet__name": "icontains"})
    device = NaturalKeyOrPKMultipleChoiceFilter(
        queryset=Device.objects.all(),
        to_field_name="name",
        label="PDU device (name or ID)",
    )

    class Meta:
        """Meta attributes for filter."""

        model = models.PduOutletStatus
        fields = "__all__"
