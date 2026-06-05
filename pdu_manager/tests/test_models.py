"""Test PduManager."""

from nautobot.apps.testing import ModelTestCases

from pdu_manager import models
from pdu_manager.tests import fixtures


class TestPduManager(ModelTestCases.BaseModelTestCase):
    """Test PduManager."""

    model = models.PduManager

    @classmethod
    def setUpTestData(cls):
        """Create test data for PduManager Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        fixtures.create_pdumanager()

    def test_create_pdumanager_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        pdumanager = models.PduManager.objects.create(name="Development")
        self.assertEqual(pdumanager.name, "Development")
        self.assertEqual(pdumanager.description, "")
        self.assertEqual(str(pdumanager), "Development")

    def test_create_pdumanager_all_fields_success(self):
        """Create PduManager with all fields."""
        pdumanager = models.PduManager.objects.create(name="Development", description="Development Test")
        self.assertEqual(pdumanager.name, "Development")
        self.assertEqual(pdumanager.description, "Development Test")
