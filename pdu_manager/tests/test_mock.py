"""Tests for the MOCK_CONNECTIONS simulation of managed-PDU CLI sessions."""

from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from pdu_manager.config import mock_connections_enabled
from pdu_manager.nornir_plays import power_control
from pdu_manager.nornir_plays.mock import simulate_command
from pdu_manager.tests import fixtures


class MockConnectionsEnabledTestCase(TestCase):
    """Tests for the MOCK_CONNECTIONS setting helper."""

    @override_settings(PLUGINS_CONFIG={"pdu_manager": {"MOCK_CONNECTIONS": True}})
    def test_enabled(self):
        self.assertTrue(mock_connections_enabled())

    @override_settings(PLUGINS_CONFIG={"pdu_manager": {"MOCK_CONNECTIONS": False}})
    def test_disabled(self):
        self.assertFalse(mock_connections_enabled())

    @override_settings(PLUGINS_CONFIG={})
    def test_absent_defaults_false(self):
        self.assertFalse(mock_connections_enabled())


class SimulateCommandTestCase(TestCase):
    """Tests for simulate_command() (stateful, cache-backed, driven by the command set)."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()  # PDU with outlet "Outlet 5" -> 5
        cls.pdu = cls.env["pdu"]
        cls.command_set = cls.env["command_set"]

    def setUp(self):
        cache.clear()

    def _simulate(self, command):
        return simulate_command(self.pdu, command, self.command_set)

    def test_action_returns_success_code(self):
        self.assertIn("E000", self._simulate("olOn 5"))

    def test_status_all_reports_outlets(self):
        output = self._simulate("olStatus all")
        self.assertIn("E000", output)
        self.assertIn("Outlet 5", output)
        self.assertRegex(output, r"5:\s*Outlet 5:\s*On")

    def test_off_then_status_reflects_state(self):
        self._simulate("olOff 5")
        self.assertRegex(self._simulate("olStatus 5"), r"5:\s*Outlet 5:\s*Off")

    def test_on_after_off_restores_state(self):
        self._simulate("olOff 5")
        self._simulate("olOn 5")
        self.assertRegex(self._simulate("olStatus 5"), r"5:\s*Outlet 5:\s*On")

    def test_reboot_leaves_outlet_on(self):
        self._simulate("olOff 5")
        self._simulate("olReboot 5")
        self.assertRegex(self._simulate("olStatus 5"), r"5:\s*Outlet 5:\s*On")

    @mock.patch("pdu_manager.nornir_plays.power_control.mock_connections_enabled", return_value=True)
    def test_run_short_circuits_to_mock(self, _enabled):
        # _run must return simulated output without opening a Nornir/SSH session.
        output = power_control._run(  # pylint: disable=protected-access
            self.pdu, "olStatus all", mock.MagicMock(), self.command_set
        )
        self.assertIn("E000", output)
        self.assertIn("Outlet 5", output)
