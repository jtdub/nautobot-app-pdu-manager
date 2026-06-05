"""Unit tests for pdu_manager."""

from nautobot.apps.testing import APIViewTestCases

from pdu_manager import models
from pdu_manager.tests import fixtures


class PduManagerAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the API viewsets for PduManager."""

    model = models.PduManager
    # Any choice fields will require the choices_fields to be set
    # to the field names in the model that are choice fields.
    choices_fields = ()

    @classmethod
    def setUpTestData(cls):
        """Create test data for PduManager API viewset."""
        super().setUpTestData()
        # Create 3 objects for the generic API test cases.
        fixtures.create_pdumanager()
        # Create 3 objects for the api test cases.
        cls.create_data = [
            {
                "name": "API Test One",
                "description": "Test One Description",
            },
            {
                "name": "API Test Two",
                "description": "Test Two Description",
            },
            {
                "name": "API Test Three",
                "description": "Test Three Description",
            },
        ]
        cls.update_data = {
            "name": "Update Test Two",
            "description": "Test Two Description",
        }
        cls.bulk_update_data = {
            "description": "Test Bulk Update Description",
        }
