"""Tests for the pdu_manager Nornir play helpers (pure functions)."""

from django.test import TestCase

from pdu_manager.nornir_plays.power_control import (
    PduCommandError,
    check_success,
    command_for,
    parse_ol_status,
)


class CommandForTestCase(TestCase):
    """Tests for command_for()."""

    def test_builds_on_command(self):
        self.assertEqual(command_for("on", [5]), "olOn 5")

    def test_builds_off_command_multiple(self):
        self.assertEqual(command_for("off", [5, 6, 11]), "olOff 5,6,11")

    def test_builds_reboot_command(self):
        self.assertEqual(command_for("reboot", [3]), "olReboot 3")

    def test_invalid_action_raises(self):
        with self.assertRaises(ValueError):
            command_for("status", [1])

    def test_empty_outlets_raises(self):
        with self.assertRaises(ValueError):
            command_for("on", [])


class CheckSuccessTestCase(TestCase):
    """Tests for check_success()."""

    def test_success_returns_output(self):
        output = "olOn 5\nE000: Success"
        self.assertEqual(check_success(output), output)

    def test_missing_code_raises(self):
        with self.assertRaises(PduCommandError):
            check_success("E102: Parameter Error")

    def test_none_raises(self):
        with self.assertRaises(PduCommandError):
            check_success(None)


class ParseOlStatusTestCase(TestCase):
    """Tests for parse_ol_status()."""

    SAMPLE = (
        "E000: Success\n"
        "     1: Core Switch: On\n"
        "     2: juniper: On\n"
        "     3: viptela: Off\n"
        "    16: Intel NUC: On\n"
    )

    def test_parses_all_outlets(self):
        statuses = parse_ol_status(self.SAMPLE)
        self.assertEqual(set(statuses), {1, 2, 3, 16})

    def test_parses_state_and_name(self):
        statuses = parse_ol_status(self.SAMPLE)
        self.assertEqual(statuses[1], {"name": "Core Switch", "state": "On"})
        self.assertEqual(statuses[3], {"name": "viptela", "state": "Off"})

    def test_ignores_non_outlet_lines(self):
        statuses = parse_ol_status("E000: Success\nNot an outlet line\n")
        self.assertEqual(statuses, {})

    def test_empty_output(self):
        self.assertEqual(parse_ol_status(""), {})
