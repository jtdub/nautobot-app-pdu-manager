"""App declaration for pdu_manager."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class PduManagerConfig(NautobotAppConfig):
    """App configuration for the pdu_manager app."""

    name = "pdu_manager"
    verbose_name = "Pdu Manager"
    version = __version__
    author = "James Williams"
    description = "Pdu Manager."
    base_url = "pdu-manager"
    required_settings = []
    # MOCK_CONNECTIONS: when True, the power-control jobs simulate APC CLI sessions instead
    # of opening SSH connections (for demos without real PDU hardware). See nornir_plays.mock.
    default_settings = {"MOCK_CONNECTIONS": False}
    docs_view_name = "plugins:pdu_manager:docs"


config = PduManagerConfig  # pylint:disable=invalid-name
