"""Tests for the PduCommandSet command-building/parsing methods used by the Nornir play."""

from django.test import TestCase

from pdu_manager.constants import APC_DEFAULT_COMMAND_SET
from pdu_manager.models import PduCommandSet


def _apc_command_set(**overrides):
    """Return an (unsaved) APC PduCommandSet, with optional field overrides."""
    return PduCommandSet(**{**APC_DEFAULT_COMMAND_SET, **overrides})


class BuildCommandTestCase(TestCase):
    """Tests for PduCommandSet.build_command()."""

    def setUp(self):
        self.command_set = _apc_command_set()

    def test_builds_on_command(self):
        self.assertEqual(self.command_set.build_command("on", [5]), "olOn 5")

    def test_builds_off_command_multiple(self):
        self.assertEqual(self.command_set.build_command("off", [5, 6, 11]), "olOff 5,6,11")

    def test_builds_reboot_command(self):
        self.assertEqual(self.command_set.build_command("reboot", [3]), "olReboot 3")

    def test_custom_separator(self):
        command_set = _apc_command_set(outlet_separator=" ")
        self.assertEqual(command_set.build_command("on", [5, 6]), "olOn 5 6")

    def test_unknown_action_raises(self):
        with self.assertRaises(ValueError):
            self.command_set.build_command("bogus", [1])

    def test_unset_reboot_command_raises(self):
        command_set = _apc_command_set(reboot_command="")
        with self.assertRaises(ValueError):
            command_set.build_command("reboot", [1])

    def test_empty_outlets_raises(self):
        with self.assertRaises(ValueError):
            self.command_set.build_command("on", [])


class StatusCommandTestCase(TestCase):
    """Tests for PduCommandSet.build_status_command()."""

    def setUp(self):
        self.command_set = _apc_command_set()

    def test_all_outlets(self):
        self.assertEqual(self.command_set.build_status_command(), "olStatus all")

    def test_specific_outlets(self):
        self.assertEqual(self.command_set.build_status_command([5, 6]), "olStatus 5,6")


class CheckSuccessTestCase(TestCase):
    """Tests for PduCommandSet.check_success()."""

    def setUp(self):
        self.command_set = _apc_command_set()

    def test_success_returns_true(self):
        self.assertTrue(self.command_set.check_success("olOn 5\nE000: Success"))

    def test_missing_code_returns_false(self):
        self.assertFalse(self.command_set.check_success("E102: Parameter Error"))

    def test_none_returns_false(self):
        self.assertFalse(self.command_set.check_success(None))

    def test_blank_success_string_always_true(self):
        command_set = _apc_command_set(success_string="")
        self.assertTrue(command_set.check_success("anything at all"))


class ParseStatusTestCase(TestCase):
    """Tests for PduCommandSet.parse_status()."""

    SAMPLE = (
        "E000: Success\n     1: Core Switch: On\n     2: juniper: On\n     3: viptela: Off\n    16: Intel NUC: On\n"
    )

    def setUp(self):
        self.command_set = _apc_command_set()

    def test_parses_all_outlets(self):
        statuses = self.command_set.parse_status(self.SAMPLE)
        self.assertEqual(set(statuses), {1, 2, 3, 16})

    def test_parses_state_and_name(self):
        statuses = self.command_set.parse_status(self.SAMPLE)
        self.assertEqual(statuses[1], {"name": "Core Switch", "state": "On"})
        self.assertEqual(statuses[3], {"name": "viptela", "state": "Off"})

    def test_ignores_non_outlet_lines(self):
        self.assertEqual(self.command_set.parse_status("E000: Success\nNot an outlet line\n"), {})

    def test_no_regex_returns_empty(self):
        command_set = _apc_command_set(status_parse_regex="")
        self.assertEqual(command_set.parse_status(self.SAMPLE), {})
