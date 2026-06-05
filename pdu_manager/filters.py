"""Filtering for pdu_manager."""

from nautobot.apps.filters import NameSearchFilterSet, NautobotFilterSet

from pdu_manager import models


class PduManagerFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for PduManager."""

    class Meta:
        """Meta attributes for filter."""

        model = models.PduManager

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
