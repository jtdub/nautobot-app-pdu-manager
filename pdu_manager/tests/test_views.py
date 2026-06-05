"""Unit tests for views."""

from nautobot.apps.testing import ViewTestCases

from pdu_manager import models
from pdu_manager.tests import fixtures


class PduManagerViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the PduManager views."""

    model = models.PduManager
    bulk_edit_data = {"description": "Bulk edit views"}
    form_data = {
        "name": "Test 1",
        "description": "Initial model",
    }

    update_data = {
        "name": "Test 2",
        "description": "Updated model",
    }

    @classmethod
    def setUpTestData(cls):
        fixtures.create_pdumanager()
