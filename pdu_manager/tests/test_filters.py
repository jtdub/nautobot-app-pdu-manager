"""Test PduManager Filter."""

from nautobot.apps.testing import FilterTestCases

from pdu_manager import filters, models
from pdu_manager.tests import fixtures


class PduManagerFilterTestCase(FilterTestCases.FilterTestCase):  # pylint: disable=too-many-ancestors
    """PduManager Filter Test Case."""

    queryset = models.PduManager.objects.all()
    filterset = filters.PduManagerFilterSet
    generic_filter_tests = (
        ("id",),
        ("created",),
        ("last_updated",),
        ("name",),
    )

    @classmethod
    def setUpTestData(cls):
        """Setup test data for PduManager Model."""
        fixtures.create_pdumanager()

    def test_q_search_name(self):
        """Test using Q search with name of PduManager."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for PduManager."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
