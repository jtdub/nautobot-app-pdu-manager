"""Tests for pdu_manager.utils device/outlet resolution."""

from django.test import TestCase

from pdu_manager.tests import fixtures
from pdu_manager.utils import (
    connected_outlet_for_device,
    is_pdu,
    outlet_index,
    resolve_pdu_and_outlets,
)


class UtilsTestCase(TestCase):
    """Tests for outlet/PDU resolution helpers."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def test_is_pdu(self):
        self.assertTrue(is_pdu(self.env["pdu"]))
        self.assertFalse(is_pdu(self.env["server"]))

    def test_outlet_index(self):
        self.assertEqual(outlet_index(self.env["outlet"]), 5)

    def test_connected_outlet_for_downstream_device(self):
        self.assertEqual(connected_outlet_for_device(self.env["server"]), self.env["outlet"])

    def test_connected_outlet_for_pdu_is_none(self):
        self.assertIsNone(connected_outlet_for_device(self.env["pdu"]))

    def test_resolve_from_downstream_device(self):
        pdu, outlet_ids = resolve_pdu_and_outlets(self.env["server"])
        self.assertEqual(pdu, self.env["pdu"])
        self.assertEqual(outlet_ids, [5])

    def test_resolve_from_pdu_with_explicit_outlet(self):
        pdu, outlet_ids = resolve_pdu_and_outlets(self.env["pdu"], self.env["outlet"])
        self.assertEqual(pdu, self.env["pdu"])
        self.assertEqual(outlet_ids, [5])

    def test_resolve_unconnected_device_raises(self):
        unconnected = self.env["server"]
        # Remove the power cable so the server is no longer fed by an outlet.
        self.env["power_port"].cable.delete()
        unconnected.refresh_from_db()
        with self.assertRaises(ValueError):
            resolve_pdu_and_outlets(unconnected)
