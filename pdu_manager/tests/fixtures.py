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
from nautobot.extras.models import Role, Status

from pdu_manager.constants import APC_DEFAULT_COMMAND_SET, APC_NETWORK_DRIVER
from pdu_manager.models import PduCommandSet, PowerOffProtection


def create_apc_command_set(platform=None):
    """Create the default APC PduCommandSet, optionally assigned to ``platform``."""
    command_set, _ = PduCommandSet.objects.get_or_create(
        name=APC_DEFAULT_COMMAND_SET["name"],
        defaults={key: value for key, value in APC_DEFAULT_COMMAND_SET.items() if key != "name"},
    )
    if platform is not None:
        command_set.platforms.add(platform)
    return command_set


def create_pdu_environment():  # pylint: disable=too-many-locals
    """Create an APC PDU, an outlet named "Outlet 5" (-> APC outlet 5), and a server cabled to it.

    Also creates the APC command set and assigns it to the PDU's platform.

    Returns:
        dict with keys ``pdu``, ``server``, ``outlet``, ``power_port``, ``platform``,
        ``role``, ``command_set``.
    """
    manufacturer = Manufacturer.objects.create(name="APC")
    platform = Platform.objects.create(name="APC AOS", network_driver=APC_NETWORK_DRIVER)
    command_set = create_apc_command_set(platform)
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

    # Name ends in "5" so outlet_index() maps it to APC outlet number 5.
    outlet = PowerOutlet.objects.create(device=pdu, name="Outlet 5")

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
        "role": role,
        "command_set": command_set,
    }


def create_pdu_with_outlets(prefix, outlet_count):
    """Create a standalone PDU device with ``outlet_count`` outlets named "Outlet 1..N".

    Each call builds its own manufacturer/type/location/role with a unique ``prefix`` so
    multiple PDUs can coexist in one test. Returns ``(pdu, [outlets])``.
    """
    manufacturer = Manufacturer.objects.create(name=f"{prefix}-mfg")
    device_type = DeviceType.objects.create(manufacturer=manufacturer, model=f"{prefix}-type")

    device_ct = ContentType.objects.get_for_model(Device)
    location_type = LocationType.objects.create(name=f"{prefix}-lt")
    location_type.content_types.add(device_ct)
    location_status = Status.objects.get_for_model(Location).first()
    location = Location.objects.create(name=f"{prefix}-loc", location_type=location_type, status=location_status)

    role = Role.objects.create(name=f"{prefix}-role")
    role.content_types.add(device_ct)
    device_status = Status.objects.get_for_model(Device).first()

    pdu = Device.objects.create(
        name=f"{prefix}-pdu",
        device_type=device_type,
        role=role,
        location=location,
        status=device_status,
    )
    outlets = [PowerOutlet.objects.create(device=pdu, name=f"Outlet {index}") for index in range(1, outlet_count + 1)]
    return pdu, outlets


def create_power_off_protection(  # pylint: disable=too-many-arguments
    name="Protect", *, enabled=True, roles=None, tenants=None, device_tags=None, devices=None
):
    """Create a PowerOffProtection rule with the given matching criteria."""
    rule = PowerOffProtection.objects.create(name=name, enabled=enabled)
    if roles:
        rule.roles.set(roles)
    if tenants:
        rule.tenants.set(tenants)
    if device_tags:
        rule.device_tags.set(device_tags)
    if devices:
        rule.devices.set(devices)
    return rule
