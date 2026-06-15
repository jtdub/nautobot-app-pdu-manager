"""API views for pdu_manager."""

from nautobot.apps.api import NautobotModelViewSet

from pdu_manager import filters, models
from pdu_manager.api import serializers


class PowerOffProtectionViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """Full REST CRUD for PowerOffProtection rules."""

    queryset = models.PowerOffProtection.objects.all()
    serializer_class = serializers.PowerOffProtectionSerializer
    filterset_class = filters.PowerOffProtectionFilterSet


class PduCommandSetViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """Full REST CRUD for PDU Command Sets."""

    queryset = models.PduCommandSet.objects.all()
    serializer_class = serializers.PduCommandSetSerializer
    filterset_class = filters.PduCommandSetFilterSet


class PduOutletStatusViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """Full REST CRUD for stored PDU outlet statuses."""

    queryset = models.PduOutletStatus.objects.all()
    serializer_class = serializers.PduOutletStatusSerializer
    filterset_class = filters.PduOutletStatusFilterSet
