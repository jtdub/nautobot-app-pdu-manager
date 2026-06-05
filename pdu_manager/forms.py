"""Forms for pdu_manager."""

from django import forms
from nautobot.apps.constants import CHARFIELD_MAX_LENGTH
from nautobot.apps.forms import NautobotBulkEditForm, NautobotFilterForm, NautobotModelForm, TagsBulkEditFormMixin

from pdu_manager import models


class PduManagerForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """PduManager creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.PduManager
        fields = "__all__"


class PduManagerBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """PduManager bulk edit form."""

    pk = forms.ModelMultipleChoiceField(queryset=models.PduManager.objects.all(), widget=forms.MultipleHiddenInput)
    description = forms.CharField(required=False, max_length=CHARFIELD_MAX_LENGTH)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class PduManagerFilterForm(NautobotFilterForm):  # pylint: disable=too-many-ancestors
    """Filter form to filter searches."""

    model = models.PduManager
    field_order = ["q", "name"]

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
