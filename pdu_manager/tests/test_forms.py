"""Test pdumanager forms."""

from django.test import TestCase

from pdu_manager import forms


class PduManagerTest(TestCase):
    """Test PduManager forms."""

    def test_specifying_all_fields_success(self):
        form = forms.PduManagerForm(
            data={
                "name": "Development",
                "description": "Development Testing",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = forms.PduManagerForm(
            data={
                "name": "Development",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_pdumanager_is_required(self):
        form = forms.PduManagerForm(data={"description": "Development Testing"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])
