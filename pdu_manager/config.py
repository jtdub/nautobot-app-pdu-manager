"""Runtime configuration helpers for pdu_manager."""

from django.conf import settings


def app_settings():
    """Return this app's ``PLUGINS_CONFIG`` dict (empty if unconfigured)."""
    return settings.PLUGINS_CONFIG.get("pdu_manager", {})


def mock_connections_enabled():
    """Return True if APC SSH sessions should be simulated instead of opened.

    Controlled by ``PLUGINS_CONFIG["pdu_manager"]["MOCK_CONNECTIONS"]`` (default False).
    Enable it for demos when no real APC PDU is reachable: the Nornir play returns canned
    APC CLI output instead of connecting over SSH. See ``nornir_plays.mock``.
    """
    return bool(app_settings().get("MOCK_CONNECTIONS", False))
