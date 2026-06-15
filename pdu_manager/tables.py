"""Tables for pdu_manager."""

import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from nautobot.apps.tables import BaseTable, BooleanColumn, ButtonsColumn, ToggleColumn

from pdu_manager import models
from pdu_manager.constants import ACTION_OFF, ACTION_ON, ACTION_REBOOT, STATE_OFF, STATE_ON, STATE_UNKNOWN

# Bootstrap-5 badge class per stored outlet state (On green, Off red, Unknown grey).
_STATE_BADGE_CLASS = {STATE_ON: "bg-success", STATE_OFF: "bg-danger", STATE_UNKNOWN: "bg-secondary"}

# Per-row power buttons rendered in the PduOutletStatus "Power" column: (action, icon, color).
_POWER_BUTTONS = (
    (ACTION_ON, "mdi-power-plug", "success", "Turn outlet on"),
    (ACTION_OFF, "mdi-power-plug-off", "danger", "Turn outlet off"),
    (ACTION_REBOOT, "mdi-restart", "warning", "Reboot outlet"),
)


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


class PduOutletStatusTable(BaseTable):
    # pylint: disable=R0903
    """Table of stored per-outlet PDU status (used by the list view and the device panel)."""

    pk = ToggleColumn()
    device = tables.Column(linkify=True)
    power_outlet = tables.Column(linkify=True, verbose_name="Outlet")
    # Linkify a scalar column to the status record so its detail URL appears in the list.
    outlet_index = tables.Column(linkify=lambda record: record.get_absolute_url(), verbose_name="Outlet #")
    state = tables.Column()
    last_polled = tables.DateTimeColumn()
    power = tables.Column(empty_values=(), orderable=False, verbose_name="Power")
    actions = ButtonsColumn(models.PduOutletStatus, buttons=("delete",))

    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = models.PduOutletStatus
        fields = (
            "pk",
            "device",
            "power_outlet",
            "outlet_index",
            "state",
            "last_polled",
            "power",
            "actions",
        )
        default_columns = (
            "pk",
            "device",
            "power_outlet",
            "outlet_index",
            "state",
            "last_polled",
            "power",
            "actions",
        )

    @staticmethod
    def render_state(value):
        """Render the state as a green (On) / red (Off) / grey (Unknown) badge."""
        css_class = _STATE_BADGE_CLASS.get(value, "bg-secondary")
        return format_html('<span class="badge {}">{}</span>', css_class, value)

    @staticmethod
    def render_power(record):
        """Render On / Off / Reboot buttons that enqueue a power action for this outlet."""
        buttons = format_html_join(
            "",
            '<a href="{}" class="btn btn-sm btn-{}" title="{}"><span class="mdi {}"></span></a>',
            (
                (
                    reverse("plugins:pdu_manager:pduoutletstatus_power", kwargs={"pk": record.pk, "action": action}),
                    color,
                    title,
                    icon,
                )
                for action, icon, color, title in _POWER_BUTTONS
            ),
        )
        return format_html('<div class="btn-group btn-group-sm" role="group">{}</div>', buttons)
