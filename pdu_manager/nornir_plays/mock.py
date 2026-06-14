"""Simulate managed-PDU CLI sessions for demos without real hardware.

When ``PLUGINS_CONFIG["pdu_manager"]["MOCK_CONNECTIONS"]`` is true, the Nornir play calls
:func:`simulate_command` instead of opening an SSH session. The verbs, success string, and
outlet separator are read from the device's :class:`~pdu_manager.models.PduCommandSet`, so
the mock follows whatever command set is in use. Outlet on/off/reboot state is tracked in the
Django cache, so a follow-up status query reflects prior actions within a demo session.

Status output is emitted in the ``"<id>: <name>: <state>"`` shape (which the default APC
command set's ``status_parse_regex`` matches); a command set whose status format differs
would need real hardware to exercise its parsing.
"""

from django.core.cache import cache

# Long enough to span a demo; state is best-effort and resets on cache eviction.
_STATE_TTL = 60 * 60 * 24
_DEFAULT_STATE = "On"


def _state_key(pdu, outlet_id):
    """Cache key for one outlet's simulated power state."""
    return f"pdu_manager:mock_outlet:{pdu.pk}:{outlet_id}"


def _get_state(pdu, outlet_id):
    """Return the simulated state ("On"/"Off") of ``outlet_id`` on ``pdu``."""
    return cache.get(_state_key(pdu, outlet_id), _DEFAULT_STATE)


def _set_state(pdu, outlet_id, state):
    """Persist the simulated state of ``outlet_id`` on ``pdu``."""
    cache.set(_state_key(pdu, outlet_id), state, _STATE_TTL)


def _outlet_names(pdu):
    """Map outlet number -> Nautobot outlet name for ``pdu``."""
    # Lazy import: keep this module importable before the Django app registry is ready.
    from pdu_manager.utils import outlet_index  # pylint: disable=import-outside-toplevel

    names = {}
    for outlet in pdu.power_outlets.all():
        index = outlet_index(outlet)
        if index is not None:
            names[index] = outlet.name
    return names


def _parse_ids(arg, separator):
    """Parse the outlet ids out of a command argument like ``5,6``."""
    return [int(token) for token in arg.split(separator) if token.strip().isdigit()]


def simulate_command(pdu, command, command_set):
    """Return canned CLI output for ``command`` against ``pdu`` using ``command_set``.

    The status verb reports the cached state of the requested outlets (or all of the PDU's
    outlets for the "all" argument); the on/off/reboot verbs update the cached state and
    return the command set's success string.
    """
    parts = command.split()
    verb = parts[0] if parts else ""
    arg = parts[1] if len(parts) > 1 else ""
    names = _outlet_names(pdu)
    success = command_set.success_string or "OK"
    separator = command_set.outlet_separator or ","

    if verb == command_set.status_command:
        if arg in ("", command_set.status_all_argument):
            outlet_ids = sorted(names)
        else:
            outlet_ids = _parse_ids(arg, separator)
        lines = [f"{success}: Success"]
        for outlet_id in outlet_ids:
            name = names.get(outlet_id, f"Outlet {outlet_id}")
            lines.append(f"{outlet_id:>6}: {name}: {_get_state(pdu, outlet_id)}")
        return "\n".join(lines) + "\n"

    new_state = None
    if verb == command_set.on_command:
        new_state = "On"
    elif verb == command_set.off_command:
        new_state = "Off"
    elif verb and verb == command_set.reboot_command:
        new_state = "On"
    if new_state is not None:
        for outlet_id in _parse_ids(arg, separator):
            _set_state(pdu, outlet_id, new_state)
    return f"{success}: Success\n"
