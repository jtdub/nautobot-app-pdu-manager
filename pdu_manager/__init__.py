"""App declaration for pdu_manager."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

# The PyPI distribution name (`nautobot-pdu-manager`) differs from the import package
# (`pdu_manager`), so look up the version by the distribution name explicitly.
__version__ = metadata.version("nautobot-pdu-manager")


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
