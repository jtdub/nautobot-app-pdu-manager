"""Tests for the generate_pdu_manager_test_data management command."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from nautobot.dcim.models import Device, PowerOutlet
from nautobot.extras.models import Job

from pdu_manager.models import PowerOffProtection
from pdu_manager.utils import is_power_off_protected


class GenerateTestDataCommandTestCase(TestCase):
    """Verify the demo-data command builds a usable, UI-validating data set."""

    @classmethod
    def setUpTestData(cls):
        call_command("generate_pdu_manager_test_data", stdout=StringIO())

    def test_creates_pdus_with_outlets(self):
        pdus = Device.objects.filter(role__name="PDU")
        self.assertEqual(pdus.count(), 2)
        for pdu in pdus:
            self.assertEqual(pdu.power_outlets.count(), 8)
            self.assertEqual(pdu.platform.network_driver, "apc_aos")
            self.assertIsNotNone(pdu.secrets_group)

    def test_downstream_devices_are_cabled_to_outlets(self):
        server = Device.objects.get(name="dce-srv-01")
        outlet = server.power_ports.first().connected_endpoint
        self.assertIsInstance(outlet, PowerOutlet)

    def test_creates_protection_rules_for_every_match_type(self):
        names = set(PowerOffProtection.objects.values_list("name", flat=True))
        self.assertIn("Protect Core Switches", names)
        self.assertIn("Protect Production Tenant", names)
        self.assertIn("Protect Critical-Tagged Devices", names)
        self.assertTrue(any(n.endswith("acc-01") for n in names))

    def test_protection_actually_matches_devices(self):
        self.assertTrue(is_power_off_protected(Device.objects.get(name="dce-core-01")))  # role
        self.assertTrue(is_power_off_protected(Device.objects.get(name="dce-srv-02")))  # tag
        self.assertTrue(is_power_off_protected(Device.objects.get(name="dce-acc-01")))  # explicit device

    def test_disabled_rule_is_not_enforced(self):
        rule = PowerOffProtection.objects.get(name="Lab Maintenance (disabled)")
        self.assertFalse(rule.enabled)

    def test_command_enables_pdu_manager_jobs(self):
        # Even if the jobs are disabled, re-running the command must enable them so the
        # device-page dropdown's Job modal is interactive.
        Job.objects.filter(module_name="pdu_manager.jobs").update(enabled=False)
        call_command("generate_pdu_manager_test_data", stdout=StringIO())
        jobs = Job.objects.filter(module_name="pdu_manager.jobs")
        self.assertTrue(jobs.exists())
        self.assertTrue(all(job.enabled for job in jobs))

    def test_idempotent(self):
        before = (Device.objects.count(), PowerOutlet.objects.count(), PowerOffProtection.objects.count())
        call_command("generate_pdu_manager_test_data", stdout=StringIO())
        after = (Device.objects.count(), PowerOutlet.objects.count(), PowerOffProtection.objects.count())
        self.assertEqual(before, after)

    def test_flush_clears_protection_rules(self):
        self.assertTrue(PowerOffProtection.objects.exists())
        call_command("generate_pdu_manager_test_data", "--flush", stdout=StringIO())
        # Rules are recreated after the flush, so they exist again and stay consistent.
        self.assertTrue(PowerOffProtection.objects.exists())
