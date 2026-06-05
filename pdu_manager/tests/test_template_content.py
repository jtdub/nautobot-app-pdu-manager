"""Tests for the pdu_manager template extension."""

from django.test import TestCase

from pdu_manager.template_content import DevicePowerControl, template_extensions


class TemplateContentTestCase(TestCase):
    """Verify the device power-control button is registered correctly."""

    def test_extension_targets_device(self):
        self.assertEqual(DevicePowerControl.model, "dcim.device")

    def test_extension_registered(self):
        self.assertIn(DevicePowerControl, template_extensions)

    def test_button_links_to_control_view(self):
        buttons = DevicePowerControl.object_detail_buttons
        self.assertEqual(len(buttons), 1)
        button = buttons[0]
        self.assertEqual(button.label, "PDU Power")
        self.assertEqual(button.link_name, "plugins:pdu_manager:device_power_control")
