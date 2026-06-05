"""Helpers for resolving APC PDUs and outlets from Nautobot devices."""

from pdu_manager.constants import PDU_OUTLET_ID_FIELD


def outlet_index(power_outlet):
    """Return the APC CLI outlet index stored on ``power_outlet``'s custom field, or None."""
    return getattr(power_outlet, "cf", {}).get(PDU_OUTLET_ID_FIELD)


def is_pdu(device):
    """Return True if ``device`` exposes power outlets (i.e. acts as a PDU)."""
    return device.power_outlets.exists()


def pdu_outlets(device):
    """Return ``device``'s own power outlets, ordered by their APC outlet index then name."""
    return device.power_outlets.all()


def connected_outlet_for_device(device):
    """Return the upstream PowerOutlet feeding ``device``, or None.

    Traverses each of the device's PowerPorts to its connected endpoint; the first endpoint
    that is a PowerOutlet is returned (a device is typically fed by a single outlet).
    """
    # Imported lazily so this module can be imported without the Django app registry ready.
    from nautobot.dcim.models import PowerOutlet  # pylint: disable=import-outside-toplevel

    for power_port in device.power_ports.all():
        endpoint = power_port.connected_endpoint
        if isinstance(endpoint, PowerOutlet):
            return endpoint
    return None


def resolve_pdu_and_outlets(device, power_outlet=None):
    """Resolve the target PDU device and outlet indexes for a power action.

    Args:
        device: The device the action was launched from (a PDU or a downstream device).
        power_outlet: Optionally, the specific PowerOutlet to act on (required when
            ``device`` is a PDU with more than one outlet).

    Returns:
        Tuple ``(pdu_device, [outlet_index, ...])``.

    Raises:
        ValueError: If no outlet can be resolved or its index custom field is unset.
    """
    if power_outlet is None and not is_pdu(device):
        # Downstream device: follow the power cable to the feeding outlet.
        power_outlet = connected_outlet_for_device(device)
        if power_outlet is None:
            raise ValueError(f"{device} is not connected to a PDU power outlet.")

    if power_outlet is None:
        raise ValueError("An outlet must be selected for a PDU with multiple outlets.")

    index = outlet_index(power_outlet)
    if index is None:
        raise ValueError(
            f"Outlet {power_outlet} has no '{PDU_OUTLET_ID_FIELD}' value set; "
            "cannot map it to an APC CLI outlet number."
        )
    return power_outlet.device, [index]
