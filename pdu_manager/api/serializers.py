"""API serializers for pdu_manager."""

from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from pdu_manager import models


class PduManagerSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """PduManager Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.PduManager
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
