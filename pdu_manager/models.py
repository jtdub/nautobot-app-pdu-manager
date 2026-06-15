"""Models for pdu_manager.

Two persisted models:

* :class:`PowerOffProtection` — the configurable replacement for the hard-coded "Core
  Infrastructure" role guard: a user defines which devices may **never** be powered off (or
  rebooted) by matching them on Role, Tenant, Tag, or explicit Device. Matching logic lives
  in :func:`pdu_manager.utils.power_off_protections_for`; enforcement happens in the
  power-control view and the jobs.
* :class:`PduCommandSet` — the per-`Platform` definition of a managed PDU's CLI commands
  (the on/off/reboot/status verbs), success marker, and status-parsing regex. The jobs
  resolve a device's command set from its PDU's Platform instead of using hard-coded APC
  commands, so additional PDU vendors can be supported with no code changes.
* :class:`PduOutletStatus` — the persisted, current on/off state of each PDU outlet. A
  Status run (the device-page button or the device-less scheduled run) upserts one row per
  outlet via :func:`pdu_manager.utils.record_outlet_statuses`; the device detail page shows
  these rows in a green (On) / red (Off) panel.
"""

import re

from django.core.exceptions import ValidationError
from django.db import models
from nautobot.apps.constants import CHARFIELD_MAX_LENGTH
from nautobot.apps.models import PrimaryModel, extras_features

from pdu_manager.constants import ACTION_OFF, ACTION_ON, ACTION_REBOOT, ACTION_STATUS, STATE_CHOICES, STATE_UNKNOWN


@extras_features("custom_links", "custom_validators", "export_templates", "graphql", "webhooks")
class PowerOffProtection(PrimaryModel):  # pylint: disable=too-many-ancestors
    """A rule that prevents matched devices from being powered off or rebooted.

    A device is protected when at least one *enabled* rule matches it through any of the
    criteria below (the criteria are OR-ed together, both within and across rules):

    * ``roles`` — the device's Role is listed.
    * ``tenants`` — the device's Tenant is listed.
    * ``device_tags`` — the device carries one of the listed Tags.
    * ``devices`` — the device is listed explicitly.

    A rule with no criteria set matches nothing.
    """

    name = models.CharField(max_length=CHARFIELD_MAX_LENGTH, unique=True)
    description = models.CharField(max_length=CHARFIELD_MAX_LENGTH, blank=True)
    enabled = models.BooleanField(
        default=True,
        help_text="Only enabled rules are enforced. Disable to suspend a rule without deleting it.",
    )
    roles = models.ManyToManyField(
        to="extras.Role",
        related_name="pdu_power_off_protections",
        blank=True,
        help_text="Protect every device assigned one of these roles.",
    )
    tenants = models.ManyToManyField(
        to="tenancy.Tenant",
        related_name="pdu_power_off_protections",
        blank=True,
        help_text="Protect every device assigned one of these tenants.",
    )
    device_tags = models.ManyToManyField(
        to="extras.Tag",
        related_name="pdu_power_off_protections",
        blank=True,
        help_text="Protect every device carrying one of these tags.",
    )
    devices = models.ManyToManyField(
        to="dcim.Device",
        related_name="pdu_power_off_protections",
        blank=True,
        help_text="Protect these specific devices.",
    )

    class Meta:
        """Meta class."""

        ordering = ["name"]
        verbose_name = "Power Off Protection"
        verbose_name_plural = "Power Off Protections"

    def __str__(self):
        """Stringify instance."""
        return self.name


@extras_features("custom_links", "custom_validators", "export_templates", "graphql", "webhooks")
class PduCommandSet(PrimaryModel):  # pylint: disable=too-many-ancestors
    """A per-Platform definition of a managed PDU's outlet-control CLI commands.

    Assign one or more `Platform`s and the verbs that map to the On/Off/Reboot/Status
    actions (e.g. APC's ``olOn``/``olOff``/``olReboot``/``olStatus``), the substring that
    marks success in command output, and an optional regex (with named groups ``id``,
    ``name``, ``state``) that parses outlet status lines. The jobs look up the command set
    for the target PDU's Platform at run time.
    """

    name = models.CharField(max_length=CHARFIELD_MAX_LENGTH, unique=True)
    description = models.CharField(max_length=CHARFIELD_MAX_LENGTH, blank=True)
    platforms = models.ManyToManyField(
        to="dcim.Platform",
        related_name="pdu_command_sets",
        blank=True,
        help_text="Platforms whose devices use these PDU commands.",
    )
    on_command = models.CharField(max_length=CHARFIELD_MAX_LENGTH, help_text="Verb to power an outlet on, e.g. `olOn`.")
    off_command = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH, help_text="Verb to power an outlet off, e.g. `olOff`."
    )
    reboot_command = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH,
        blank=True,
        help_text="Verb to reboot an outlet, e.g. `olReboot`. Leave blank if reboot is unsupported.",
    )
    status_command = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH, help_text="Verb to read outlet status, e.g. `olStatus`."
    )
    status_all_argument = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH,
        default="all",
        blank=True,
        help_text="Argument that queries every outlet, e.g. `all` for `olStatus all`.",
    )
    outlet_separator = models.CharField(
        max_length=8,
        default=",",
        help_text="Separator joining multiple outlet numbers, e.g. `,` for `olOn 5,6`.",
    )
    success_string = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH,
        default="E000",
        blank=True,
        help_text="Substring present in command output on success, e.g. `E000`. Blank skips the check.",
    )
    status_parse_regex = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH,
        blank=True,
        help_text="Regex with named groups `id`, `name`, `state` to parse each status line.",
    )

    class Meta:
        """Meta class."""

        ordering = ["name"]
        verbose_name = "PDU Command Set"
        verbose_name_plural = "PDU Command Sets"

    def __str__(self):
        """Stringify instance."""
        return self.name

    def clean(self):
        """Validate that ``status_parse_regex`` compiles."""
        super().clean()
        if self.status_parse_regex:
            try:
                re.compile(self.status_parse_regex)
            except re.error as error:
                raise ValidationError({"status_parse_regex": f"Invalid regular expression: {error}"}) from error

    def command_for_action(self, action):
        """Return the configured verb for ``action`` (None if unset)."""
        return {
            ACTION_ON: self.on_command,
            ACTION_OFF: self.off_command,
            ACTION_REBOOT: self.reboot_command,
            ACTION_STATUS: self.status_command,
        }.get(action)

    def _join(self, outlet_ids):
        """Join outlet numbers with the configured separator."""
        return self.outlet_separator.join(str(int(outlet_id)) for outlet_id in outlet_ids)

    def build_command(self, action, outlet_ids):
        """Build the CLI command for an on/off/reboot ``action`` against ``outlet_ids``."""
        verb = self.command_for_action(action)
        if not verb:
            raise ValueError(f"Command set '{self.name}' defines no command for action '{action}'.")
        if not outlet_ids:
            raise ValueError("At least one outlet id is required.")
        return f"{verb} {self._join(outlet_ids)}"

    def build_status_command(self, outlet_ids=None):
        """Build the status command for ``outlet_ids`` (all outlets if falsy)."""
        if not self.status_command:
            raise ValueError(f"Command set '{self.name}' defines no status command.")
        if not outlet_ids:
            return f"{self.status_command} {self.status_all_argument}".rstrip()
        return f"{self.status_command} {self._join(outlet_ids)}"

    def check_success(self, output):
        """Return True if ``output`` indicates success (or no success string is configured)."""
        if not self.success_string:
            return True
        return self.success_string in (output or "")

    def parse_status(self, output):
        """Parse ``output`` into ``{outlet_id: {"name": str, "state": str}}`` using the regex."""
        if not self.status_parse_regex:
            return {}
        pattern = re.compile(self.status_parse_regex, re.IGNORECASE)
        statuses = {}
        for line in (output or "").splitlines():
            match = pattern.match(line)
            if not match:
                continue
            groups = match.groupdict()
            try:
                outlet_id = int(groups["id"])
            except (KeyError, TypeError, ValueError):
                continue
            statuses[outlet_id] = {
                "name": (groups.get("name") or "").strip(),
                "state": (groups.get("state") or "").capitalize(),
            }
        return statuses


@extras_features("custom_links", "custom_validators", "export_templates", "graphql", "webhooks")
class PduOutletStatus(PrimaryModel):  # pylint: disable=too-many-ancestors
    """The last-polled on/off state of a single PDU outlet.

    One row per outlet (keyed on ``power_outlet``): a Status run upserts the row with the
    state parsed from the PDU's CLI output and the time it was polled. ``device`` (the PDU)
    and ``outlet_index`` (the APC CLI outlet number) are denormalized from the outlet so the
    device-page panel and the list view can filter/sort without re-deriving them.
    """

    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="pdu_outlet_statuses",
        help_text="The PDU whose outlet this status belongs to.",
    )
    power_outlet = models.OneToOneField(
        to="dcim.PowerOutlet",
        on_delete=models.CASCADE,
        related_name="pdu_outlet_status",
        help_text="The PDU outlet this status describes.",
    )
    outlet_index = models.PositiveIntegerField(
        help_text="The APC CLI outlet number parsed from the outlet name.",
    )
    state = models.CharField(
        max_length=16,
        choices=STATE_CHOICES,
        default=STATE_UNKNOWN,
        help_text="The last-polled outlet state (On / Off / Unknown).",
    )
    last_polled = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this outlet's state was last read from the PDU.",
    )

    class Meta:
        """Meta class."""

        ordering = ["device", "outlet_index"]
        verbose_name = "PDU Outlet Status"
        verbose_name_plural = "PDU Outlet Statuses"

    def __str__(self):
        """Stringify instance."""
        return f"{self.power_outlet} = {self.state}"
