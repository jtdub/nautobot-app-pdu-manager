"""Create fixtures for tests."""

from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import (
    Cable,
    Device,
    DeviceType,
    Location,
    LocationType,
    Manufacturer,
    Platform,
    PowerOutlet,
    PowerPort,
)
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField, Role, Status

from pdu_manager.constants import APC_NETWORK_DRIVER, PDU_OUTLET_ID_FIELD
from pdu_manager.models import PduManager


def create_pdumanager():
    """Fixture to create necessary number of PduManager for tests."""
    PduManager.objects.create(name="Test One")
    PduManager.objects.create(name="Test Two")
    PduManager.objects.create(name="Test Three")


def ensure_pdu_outlet_custom_field():
    """Ensure the pdu_outlet_id CustomField exists and applies to PowerOutlet.

    The app normally creates this via the ``nautobot_database_ready`` signal; tests call
    this so they do not depend on signal timing.
    """
    field, _ = CustomField.objects.get_or_create(
        key=PDU_OUTLET_ID_FIELD,
        defaults={"type": CustomFieldTypeChoices.TYPE_INTEGER, "label": "PDU Outlet ID"},
    )
    field.content_types.add(ContentType.objects.get_for_model(PowerOutlet))
    return field


def create_pdu_environment():  # pylint: disable=too-many-locals
    """Create an APC PDU, an outlet (index 5), and a server cabled to that outlet.

    Returns:
        dict with keys ``pdu``, ``server``, ``outlet``, ``power_port``, ``platform``.
    """
    ensure_pdu_outlet_custom_field()

    manufacturer = Manufacturer.objects.create(name="APC")
    platform = Platform.objects.create(name="APC AOS", network_driver=APC_NETWORK_DRIVER)
    pdu_type = DeviceType.objects.create(manufacturer=manufacturer, model="AP8xxx")
    server_type = DeviceType.objects.create(manufacturer=manufacturer, model="Server")

    device_ct = ContentType.objects.get_for_model(Device)
    location_type = LocationType.objects.create(name="Site")
    location_type.content_types.add(device_ct)

    location_status = Status.objects.get_for_model(Location).first()
    location = Location.objects.create(name="DC1", location_type=location_type, status=location_status)

    role = Role.objects.create(name="pdu-test-role")
    role.content_types.add(device_ct)
    device_status = Status.objects.get_for_model(Device).first()

    pdu = Device.objects.create(
        name="pdu1",
        device_type=pdu_type,
        role=role,
        location=location,
        status=device_status,
        platform=platform,
    )
    server = Device.objects.create(
        name="server1",
        device_type=server_type,
        role=role,
        location=location,
        status=device_status,
    )

    outlet = PowerOutlet.objects.create(device=pdu, name="Outlet 5")
    outlet.cf[PDU_OUTLET_ID_FIELD] = 5
    outlet.validated_save()

    power_port = PowerPort.objects.create(device=server, name="PSU1")

    cable_status = Status.objects.get_for_model(Cable).first()
    cable = Cable(termination_a=power_port, termination_b=outlet, status=cable_status)
    cable.validated_save()

    return {
        "pdu": pdu,
        "server": server,
        "outlet": outlet,
        "power_port": power_port,
        "platform": platform,
    }
