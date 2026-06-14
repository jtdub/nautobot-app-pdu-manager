"""API serializers for pdu_manager."""

from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from pdu_manager import models


class PowerOffProtectionSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """Serializer for the PowerOffProtection model."""

    class Meta:
        """Meta attributes."""

        model = models.PowerOffProtection
        fields = "__all__"


class PduCommandSetSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """Serializer for the PduCommandSet model."""

    class Meta:
        """Meta attributes."""

        model = models.PduCommandSet
        fields = "__all__"
