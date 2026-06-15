"""API tests for pdu_manager."""

from nautobot.apps.testing import APIViewTestCases

from pdu_manager import models
from pdu_manager.tests import fixtures


class PowerOffProtectionAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Full CRUD API tests for PowerOffProtection."""

    model = models.PowerOffProtection
    choices_fields = ()

    create_data = [
        {"name": "API One", "description": "first", "enabled": True},
        {"name": "API Two", "description": "second", "enabled": False},
        {"name": "API Three"},
    ]
    update_data = {"name": "Updated", "description": "updated", "enabled": False}
    bulk_update_data = {"enabled": False, "description": "bulk"}

    @classmethod
    def setUpTestData(cls):
        """Create the baseline objects the generic API test cases expect."""
        super().setUpTestData()
        env = fixtures.create_pdu_environment()
        fixtures.create_power_off_protection("Seed One", roles=[env["role"]], devices=[env["server"]])
        fixtures.create_power_off_protection("Seed Two")
        fixtures.create_power_off_protection("Seed Three")


class PduCommandSetAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Full CRUD API tests for PduCommandSet."""

    model = models.PduCommandSet
    choices_fields = ()

    create_data = [
        {"name": "Vendor One", "on_command": "on", "off_command": "off", "status_command": "stat"},
        {
            "name": "Vendor Two",
            "on_command": "pon",
            "off_command": "poff",
            "reboot_command": "preboot",
            "status_command": "pstat",
        },
        {"name": "Vendor Three", "on_command": "1on", "off_command": "1off", "status_command": "1stat"},
    ]
    update_data = {"name": "Updated", "on_command": "newon", "off_command": "newoff", "status_command": "newstat"}
    bulk_update_data = {"success_string": "OK"}

    @classmethod
    def setUpTestData(cls):
        """Create the baseline objects the generic API test cases expect."""
        super().setUpTestData()
        for index in range(3):
            models.PduCommandSet.objects.create(
                name=f"Seed {index}", on_command="on", off_command="off", status_command="stat"
            )


class PduOutletStatusAPIViewTest(APIViewTestCases.APIViewTestCase):
    # pylint: disable=too-many-ancestors
    """Full CRUD API tests for PduOutletStatus."""

    model = models.PduOutletStatus
    choices_fields = ["state"]
    update_data = {"state": "Off"}
    bulk_update_data = {"state": "Off"}

    @classmethod
    def setUpTestData(cls):
        """Seed three statuses and reserve three free outlets for the create tests."""
        super().setUpTestData()
        pdu, outlets = fixtures.create_pdu_with_outlets("api-status", 6)
        for index in range(3):
            models.PduOutletStatus.objects.create(
                device=pdu, power_outlet=outlets[index], outlet_index=index + 1, state="On"
            )
        cls.create_data = [
            {"device": pdu.pk, "power_outlet": outlets[3].pk, "outlet_index": 4, "state": "On"},
            {"device": pdu.pk, "power_outlet": outlets[4].pk, "outlet_index": 5, "state": "Off"},
            {"device": pdu.pk, "power_outlet": outlets[5].pk, "outlet_index": 6, "state": "Unknown"},
        ]
