"""Signal handlers for the pdu_manager app."""

from pdu_manager.constants import PDU_OUTLET_ID_FIELD


def create_pdu_outlet_custom_field(sender, *, apps, **kwargs):  # pylint: disable=unused-argument
    """Create the ``pdu_outlet_id`` CustomField on dcim.PowerOutlet on database ready.

    This runs via the ``nautobot_database_ready`` signal, so models must be looked up
    through ``apps.get_model`` rather than imported directly.
    """
    # Import here so this module can be imported without a configured app registry.
    from nautobot.extras.choices import CustomFieldTypeChoices  # pylint: disable=import-outside-toplevel

    # Model classes intentionally use PascalCase local names (Django convention).
    ContentType = apps.get_model("contenttypes", "ContentType")  # pylint: disable=invalid-name
    PowerOutlet = apps.get_model("dcim", "PowerOutlet")  # pylint: disable=invalid-name
    CustomField = apps.get_model("extras", "CustomField")  # pylint: disable=invalid-name

    field, _ = CustomField.objects.update_or_create(
        key=PDU_OUTLET_ID_FIELD,
        defaults={
            "type": CustomFieldTypeChoices.TYPE_INTEGER,
            "label": "PDU Outlet ID",
            "description": "Numeric outlet index used by the APC PDU CLI (e.g. `olOn 5`).",
        },
    )
    field.content_types.add(ContentType.objects.get_for_model(PowerOutlet))
