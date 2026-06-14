"""Tables for pdu_manager."""

import django_tables2 as tables
from nautobot.apps.tables import BaseTable, BooleanColumn, ButtonsColumn, ToggleColumn

from pdu_manager import models


class PowerOffProtectionTable(BaseTable):
    # pylint: disable=R0903
    """Table for the PowerOffProtection list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    enabled = BooleanColumn()
    roles = tables.Column(empty_values=(), orderable=False, verbose_name="Roles")
    tenants = tables.Column(empty_values=(), orderable=False, verbose_name="Tenants")
    device_tags = tables.Column(empty_values=(), orderable=False, verbose_name="Device Tags")
    devices = tables.Column(empty_values=(), orderable=False, verbose_name="Devices")
    actions = ButtonsColumn(models.PowerOffProtection)

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.PowerOffProtection
        fields = (
            "pk",
            "name",
            "enabled",
            "description",
            "roles",
            "tenants",
            "device_tags",
            "devices",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "enabled",
            "roles",
            "tenants",
            "device_tags",
            "devices",
            "actions",
        )

    @staticmethod
    def render_roles(record):
        """Show the number of roles matched by this rule."""
        return record.roles.count()

    @staticmethod
    def render_tenants(record):
        """Show the number of tenants matched by this rule."""
        return record.tenants.count()

    @staticmethod
    def render_device_tags(record):
        """Show the number of device tags matched by this rule."""
        return record.device_tags.count()

    @staticmethod
    def render_devices(record):
        """Show the number of devices explicitly matched by this rule."""
        return record.devices.count()


class PduCommandSetTable(BaseTable):
    # pylint: disable=R0903
    """Table for the PDU Command Set list view."""

    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    platforms = tables.Column(empty_values=(), orderable=False, verbose_name="Platforms")
    actions = ButtonsColumn(models.PduCommandSet)

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.PduCommandSet
        fields = (
            "pk",
            "name",
            "platforms",
            "on_command",
            "off_command",
            "reboot_command",
            "status_command",
            "success_string",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "platforms",
            "on_command",
            "off_command",
            "reboot_command",
            "status_command",
            "actions",
        )

    @staticmethod
    def render_platforms(record):
        """Show the number of platforms assigned to this command set."""
        return record.platforms.count()
