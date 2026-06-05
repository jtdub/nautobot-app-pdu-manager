"""API views for pdu_manager."""

from nautobot.apps.api import NautobotModelViewSet

from pdu_manager import filters, models
from pdu_manager.api import serializers


class PduManagerViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """PduManager viewset."""

    queryset = models.PduManager.objects.all()
    serializer_class = serializers.PduManagerSerializer
    filterset_class = filters.PduManagerFilterSet

    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]
