"""UI view tests for pdu_manager."""

from nautobot.apps.testing import ViewTestCases

from pdu_manager import models
from pdu_manager.tests import fixtures


class PowerOffProtectionViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Exercise the list/detail/add/edit/delete/bulk views for PowerOffProtection."""

    model = models.PowerOffProtection
    bulk_edit_data = {"description": "Bulk edited"}
    form_data = {
        "name": "View One",
        "description": "created via the form",
        "enabled": True,
    }
    update_data = {
        "name": "View Two",
        "description": "updated via the form",
        "enabled": False,
    }

    @classmethod
    def setUpTestData(cls):
        fixtures.create_power_off_protection("Existing One")
        fixtures.create_power_off_protection("Existing Two")
        fixtures.create_power_off_protection("Existing Three")


class PduCommandSetViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Exercise the list/detail/add/edit/delete/bulk views for PduCommandSet."""

    model = models.PduCommandSet
    bulk_edit_data = {"success_string": "OK"}
    form_data = {
        "name": "View One",
        "on_command": "on",
        "off_command": "off",
        "status_command": "stat",
        "outlet_separator": ",",
    }
    update_data = {
        "name": "View Two",
        "on_command": "newon",
        "off_command": "newoff",
        "status_command": "newstat",
        "outlet_separator": ",",
    }

    @classmethod
    def setUpTestData(cls):
        for index in range(3):
            models.PduCommandSet.objects.create(
                name=f"Existing {index}", on_command="on", off_command="off", status_command="stat"
            )
