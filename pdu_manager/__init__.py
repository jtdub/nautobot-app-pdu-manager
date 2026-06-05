"""App declaration for pdu_manager."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig, nautobot_database_ready

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
    default_settings = {}
    docs_view_name = "plugins:pdu_manager:docs"
    searchable_models = ["pdumanager"]

    def ready(self):
        """Connect signal handlers once the app registry is ready."""
        super().ready()

        from pdu_manager.signals import create_pdu_outlet_custom_field  # pylint: disable=import-outside-toplevel

        nautobot_database_ready.connect(create_pdu_outlet_custom_field, sender=self)


config = PduManagerConfig  # pylint:disable=invalid-name
