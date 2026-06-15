"""Helpers for resolving APC PDUs and outlets from Nautobot devices."""

import re

from pdu_manager.constants import PROTECTED_ACTIONS

# The APC CLI outlet number is taken from the trailing integer of the Nautobot outlet
# name, e.g. "Power Outlet 17" -> 17 (the "17" in `olOn 17`). Names without a trailing
# integer cannot be mapped to an APC outlet number.
_OUTLET_NUMBER_RE = re.compile(r"(\d+)\s*$")


def outlet_index(power_outlet):
    """Return the APC CLI outlet number parsed from ``power_outlet``'s name, or None.

    Returns the trailing integer of the outlet name, or None if the name has no trailing
    integer (callers treat None as "cannot control this outlet").
    """
    match = _OUTLET_NUMBER_RE.search(getattr(power_outlet, "name", "") or "")
    return int(match.group(1)) if match else None


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
            f"Outlet name {power_outlet.name!r} has no trailing outlet number; "
            "cannot map it to an APC CLI outlet number."
        )
    return power_outlet.device, [index]


def command_set_for(pdu):
    """Return the PduCommandSet assigned to ``pdu``'s Platform.

    Raises:
        ValueError: If the PDU has no Platform, or no command set is assigned to it.
    """
    # Imported lazily so this module stays importable before the app registry is ready.
    from pdu_manager.models import PduCommandSet  # pylint: disable=import-outside-toplevel

    platform = pdu.platform
    if platform is None:
        raise ValueError(f"{pdu.name} has no Platform assigned; cannot resolve its PDU command set.")
    command_set = PduCommandSet.objects.filter(platforms=platform).first()
    if command_set is None:
        raise ValueError(
            f"No PDU command set is assigned to Platform '{platform.name}'. "
            "Create one under Apps > PDU Manager > PDU Command Sets and assign the platform."
        )
    return command_set


def _upsert_outlet_statuses(pdu, state_for_index):
    """Upsert PduOutletStatus rows for ``pdu``'s outlets, deriving each state from its index.

    ``state_for_index(index)`` returns the state to store for the outlet, or None to leave
    that outlet untouched. Outlets whose name has no trailing number (no index) are skipped.
    The single choke point both :func:`record_outlet_statuses` and
    :func:`record_outlet_action_result` share.

    Returns:
        The list of created/updated PduOutletStatus rows.
    """
    # Imported lazily so this module stays importable before the app registry is ready.
    from django.utils import timezone  # pylint: disable=import-outside-toplevel

    from pdu_manager.models import PduOutletStatus  # pylint: disable=import-outside-toplevel

    now = timezone.now()
    recorded = []
    for outlet in pdu.power_outlets.all():
        index = outlet_index(outlet)
        if index is None:
            continue
        state = state_for_index(index)
        if state is None:
            continue
        status, _ = PduOutletStatus.objects.update_or_create(
            power_outlet=outlet,
            defaults={"device": pdu, "outlet_index": index, "state": state, "last_polled": now},
        )
        recorded.append(status)
    return recorded


def record_outlet_statuses(pdu, statuses):
    """Upsert :class:`~pdu_manager.models.PduOutletStatus` rows from a Status run.

    ``statuses`` is the ``{outlet_index: {"name", "state"}}`` dict returned by
    ``power_control.run_status``. For each of ``pdu``'s outlets whose index appears in
    ``statuses``, the matching row is created or updated with the normalized state.

    Returns:
        The list of created/updated PduOutletStatus rows.
    """
    from pdu_manager.constants import STATE_OFF, STATE_ON, STATE_UNKNOWN  # pylint: disable=import-outside-toplevel

    def state_for_index(index):
        if index not in statuses:
            return None
        raw_state = (statuses[index].get("state") or "").strip().lower()
        return {"on": STATE_ON, "off": STATE_OFF}.get(raw_state, STATE_UNKNOWN)

    return _upsert_outlet_statuses(pdu, state_for_index)


def record_outlet_action_result(pdu, outlet_ids, action):
    """Update stored status for the outlets a power action just changed.

    Called after a power action (on/off/reboot) reports success, so the device-page panel
    reflects the change immediately without waiting for the next Status poll. The resulting
    state is derived from the action via ``ACTION_TO_STATE``. Only the outlets named in
    ``outlet_ids`` are touched.

    Returns:
        The list of created/updated PduOutletStatus rows.
    """
    from pdu_manager.constants import ACTION_TO_STATE, STATE_UNKNOWN  # pylint: disable=import-outside-toplevel

    targets = set(outlet_ids or [])
    state = ACTION_TO_STATE.get(action, STATE_UNKNOWN)
    return _upsert_outlet_statuses(pdu, lambda index: state if index in targets else None)


def downstream_devices_for_outlet(power_outlet):
    """Return the device(s) fed by ``power_outlet`` via its connected power port, if any.

    A PowerOutlet connects to a downstream device's PowerPort; ``connected_endpoint`` is
    that PowerPort, whose ``.device`` is the powered device.
    """
    endpoint = getattr(power_outlet, "connected_endpoint", None)
    device = getattr(endpoint, "device", None)
    return [device] if device is not None else []


def power_off_protections_for(device):
    """Return the enabled PowerOffProtection rules that match ``device``.

    Criteria (role / tenant / tag / explicit device) are OR-ed together. A device with no
    role, tenant, or tags can still match an explicit-device rule.
    """
    # Imported lazily so this module stays importable before the app registry is ready.
    from django.db.models import Q  # pylint: disable=import-outside-toplevel

    from pdu_manager.models import PowerOffProtection  # pylint: disable=import-outside-toplevel

    match = Q(devices=device.pk)
    if device.role_id:
        match |= Q(roles=device.role_id)
    if device.tenant_id:
        match |= Q(tenants=device.tenant_id)
    tag_ids = list(device.tags.values_list("pk", flat=True))
    if tag_ids:
        match |= Q(device_tags__in=tag_ids)
    return PowerOffProtection.objects.filter(Q(enabled=True) & match).distinct()


def is_power_off_protected(device):
    """Return True if ``device`` matches any enabled PowerOffProtection rule."""
    return power_off_protections_for(device).exists()


def blocked_protected_devices(invoked_device, action, outlets=None):
    """Return the protected devices that would block ``action``, or an empty list.

    Considers the device the action was invoked from plus the downstream devices fed by
    any ``outlets`` being acted on (so toggling a PDU outlet that feeds a protected device
    is refused too). Non power-removing actions (On/Status) are never blocked.
    """
    if action not in PROTECTED_ACTIONS:
        return []
    candidates = {invoked_device.pk: invoked_device}
    for outlet in outlets or []:
        for device in downstream_devices_for_outlet(outlet):
            candidates[device.pk] = device
    return [device for device in candidates.values() if is_power_off_protected(device)]
