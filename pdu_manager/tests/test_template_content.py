"""Tests for the pdu_manager template extension (built-in PDU power dropdown)."""

from django.test import TestCase
from nautobot.apps.ui import DropdownButton

from pdu_manager.template_content import DevicePowerControl, template_extensions


class TemplateContentTestCase(TestCase):
    """Verify the device power-control dropdown is declared correctly."""

    def test_extension_targets_device(self):
        self.assertEqual(DevicePowerControl.model, "dcim.device")

    def test_extension_registered(self):
        self.assertIn(DevicePowerControl, template_extensions)

    def test_single_power_dropdown(self):
        buttons = DevicePowerControl.object_detail_buttons
        self.assertEqual(len(buttons), 1)
        self.assertIsInstance(buttons[0], DropdownButton)
        self.assertEqual(buttons[0].label, "PDU Power")
        self.assertEqual(buttons[0].icon, "mdi-power")

    def test_dropdown_has_all_four_actions(self):
        dropdown = DevicePowerControl.object_detail_buttons[0]
        labels = [child.label for child in dropdown.children]
        self.assertEqual(labels, ["Status", "On", "Off", "Reboot"])

    def test_each_item_launches_its_action_job(self):
        dropdown = DevicePowerControl.object_detail_buttons[0]
        class_paths = {child.label: child.class_path for child in dropdown.children}
        self.assertEqual(class_paths["Status"], "pdu_manager.jobs.PowerStatusJob")
        self.assertEqual(class_paths["On"], "pdu_manager.jobs.PowerOnJob")
        self.assertEqual(class_paths["Off"], "pdu_manager.jobs.PowerOffJob")
        self.assertEqual(class_paths["Reboot"], "pdu_manager.jobs.PowerRebootJob")

    def test_dropdown_requires_run_job_permission(self):
        dropdown = DevicePowerControl.object_detail_buttons[0]
        self.assertIn("extras.run_job", dropdown.required_permissions)
