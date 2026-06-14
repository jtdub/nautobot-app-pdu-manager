"""Tests for the pdu_manager models and the protection/command-set helpers."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from nautobot.dcim.models import Device, PowerOutlet
from nautobot.extras.models import Tag

from pdu_manager.models import PduCommandSet, PowerOffProtection
from pdu_manager.tests import fixtures
from pdu_manager.utils import (
    blocked_protected_devices,
    command_set_for,
    is_power_off_protected,
    power_off_protections_for,
)


class PowerOffProtectionMatchingTestCase(TestCase):
    """Verify which devices a PowerOffProtection rule protects, and the action guard."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()
        cls.server = cls.env["server"]
        cls.pdu = cls.env["pdu"]

    def test_unprotected_by_default(self):
        self.assertFalse(is_power_off_protected(self.server))
        self.assertEqual(list(power_off_protections_for(self.server)), [])

    def test_match_by_role(self):
        rule = fixtures.create_power_off_protection("by-role", roles=[self.env["role"]])
        self.assertTrue(is_power_off_protected(self.server))
        self.assertIn(rule, power_off_protections_for(self.server))

    def test_match_by_explicit_device(self):
        fixtures.create_power_off_protection("by-device", devices=[self.server])
        self.assertTrue(is_power_off_protected(self.server))

    def test_match_by_tag(self):
        tag = Tag.objects.create(name="critical")
        tag.content_types.add(ContentType.objects.get_for_model(Device))
        self.server.tags.add(tag)
        fixtures.create_power_off_protection("by-tag", device_tags=[tag])
        self.assertTrue(is_power_off_protected(self.server))

    def test_disabled_rule_does_not_protect(self):
        fixtures.create_power_off_protection("disabled", enabled=False, devices=[self.server])
        self.assertFalse(is_power_off_protected(self.server))

    def test_blocked_only_for_power_removing_actions(self):
        fixtures.create_power_off_protection("by-device", devices=[self.server])
        self.assertEqual(blocked_protected_devices(self.server, "on"), [])
        self.assertEqual(blocked_protected_devices(self.server, "status"), [])
        self.assertEqual(blocked_protected_devices(self.server, "off"), [self.server])
        self.assertEqual(blocked_protected_devices(self.server, "reboot"), [self.server])

    def test_blocked_via_pdu_outlet_downstream_device(self):
        """Acting on the PDU outlet that feeds a protected device is also blocked."""
        fixtures.create_power_off_protection("by-device", devices=[self.server])
        # Re-fetch the outlet so its cable-path cache is populated, as the view/job do.
        outlet = PowerOutlet.objects.get(pk=self.env["outlet"].pk)
        blocked = blocked_protected_devices(self.pdu, "off", [outlet])
        self.assertIn(self.server, blocked)

    def test_str(self):
        rule = PowerOffProtection.objects.create(name="my-rule")
        self.assertEqual(str(rule), "my-rule")


class PduCommandSetTestCase(TestCase):
    """Tests for the PduCommandSet model and command_set_for resolver."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def test_str(self):
        self.assertEqual(str(self.env["command_set"]), "APC AOS")

    def test_clean_rejects_invalid_regex(self):
        command_set = PduCommandSet(
            name="bad", on_command="x", off_command="y", status_command="z", status_parse_regex="(unclosed"
        )
        with self.assertRaises(ValidationError):
            command_set.clean()

    def test_command_set_for_resolves_by_platform(self):
        self.assertEqual(command_set_for(self.env["pdu"]), self.env["command_set"])

    def test_command_set_for_raises_when_unassigned(self):
        self.env["command_set"].platforms.clear()
        with self.assertRaises(ValueError):
            command_set_for(self.env["pdu"])
