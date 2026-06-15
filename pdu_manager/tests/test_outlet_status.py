"""Tests for the PduOutletStatus model, its persistence helper, and the Status sync job."""

import uuid
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from nautobot.core.testing import TestCase as NautobotTestCase

from pdu_manager.constants import STATE_OFF, STATE_ON, STATE_UNKNOWN
from pdu_manager.jobs import PowerControlJob, PowerStatusJob
from pdu_manager.models import PduOutletStatus
from pdu_manager.tests import fixtures
from pdu_manager.utils import record_outlet_action_result, record_outlet_statuses


class RecordOutletStatusesTestCase(TestCase):
    """Verify ``record_outlet_statuses`` upserts one row per outlet with the parsed state."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def test_creates_row_with_normalized_state(self):
        record_outlet_statuses(self.env["pdu"], {5: {"name": "Outlet 5", "state": "On"}})
        status = PduOutletStatus.objects.get(power_outlet=self.env["outlet"])
        self.assertEqual(status.device, self.env["pdu"])
        self.assertEqual(status.outlet_index, 5)
        self.assertEqual(status.state, STATE_ON)
        self.assertIsNotNone(status.last_polled)

    def test_upserts_existing_row(self):
        record_outlet_statuses(self.env["pdu"], {5: {"name": "Outlet 5", "state": "On"}})
        record_outlet_statuses(self.env["pdu"], {5: {"name": "Outlet 5", "state": "Off"}})
        self.assertEqual(PduOutletStatus.objects.count(), 1)
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_OFF)

    def test_unrecognized_state_is_unknown(self):
        record_outlet_statuses(self.env["pdu"], {5: {"name": "Outlet 5", "state": "wonky"}})
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_UNKNOWN)

    def test_outlet_absent_from_statuses_is_skipped(self):
        record_outlet_statuses(self.env["pdu"], {99: {"name": "Other", "state": "On"}})
        self.assertEqual(PduOutletStatus.objects.count(), 0)


class RecordOutletActionResultTestCase(TestCase):
    """Verify a power action updates the stored state for just the affected outlet(s)."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def test_off_sets_off(self):
        record_outlet_action_result(self.env["pdu"], [5], "off")
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_OFF)

    def test_on_sets_on(self):
        record_outlet_action_result(self.env["pdu"], [5], "on")
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_ON)

    def test_reboot_ends_on(self):
        record_outlet_action_result(self.env["pdu"], [5], "reboot")
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_ON)

    def test_only_named_outlets_are_touched(self):
        record_outlet_action_result(self.env["pdu"], [99], "off")
        self.assertEqual(PduOutletStatus.objects.count(), 0)


class PowerActionJobUpdatesStatusTestCase(TestCase):
    """Verify the power-control job persists the new outlet state after a successful action."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_off_action_marks_outlet_off(self, _mock_run):
        job = PowerControlJob()
        job.logger = mock.MagicMock()
        job.run(device=self.env["server"], action="off")
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_OFF)


class PowerStatusJobPersistenceTestCase(TestCase):
    """Verify the Status job persists results and supports a device-less all-PDU run."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def _job(self):
        job = PowerStatusJob()
        job.logger = mock.MagicMock()
        return job

    @mock.patch("pdu_manager.jobs.power_control.run_status")
    def test_status_for_device_persists_state(self, mock_status):
        mock_status.return_value = {5: {"name": "Outlet 5", "state": "Off"}}
        job = self._job()
        job.run(device=self.env["pdu"])
        mock_status.assert_called_once_with(job, self.env["pdu"])
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_OFF)

    @mock.patch("pdu_manager.jobs.power_control.run_status")
    def test_deviceless_run_refreshes_every_pdu(self, mock_status):
        mock_status.return_value = {5: {"name": "Outlet 5", "state": "On"}}
        job = self._job()
        message = job.run()
        mock_status.assert_called_once_with(job, self.env["pdu"])
        self.assertIn("1/1", message)
        self.assertEqual(PduOutletStatus.objects.get(power_outlet=self.env["outlet"]).state, STATE_ON)

    @mock.patch("pdu_manager.jobs.power_control.run_status", side_effect=ValueError("no command set"))
    def test_deviceless_run_skips_pdus_that_error(self, _mock_status):
        job = self._job()
        message = job.run()
        self.assertIn("0/1", message)
        self.assertEqual(PduOutletStatus.objects.count(), 0)


class OutletPowerActionViewTestCase(NautobotTestCase):
    """Verify the status table's per-row On/Off/Reboot buttons enqueue the right action."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()
        cls.status = PduOutletStatus.objects.create(
            device=cls.env["pdu"], power_outlet=cls.env["outlet"], outlet_index=5, state=STATE_ON
        )

    def _url(self, action):
        return reverse("plugins:pdu_manager:pduoutletstatus_power", kwargs={"pk": self.status.pk, "action": action})

    @mock.patch("pdu_manager.views.JobResult.enqueue_job")
    def test_action_enqueues_power_control_job(self, mock_enqueue):
        mock_enqueue.return_value = mock.Mock(pk=uuid.uuid4())
        self.add_permissions("extras.run_job", "pdu_manager.view_pduoutletstatus")
        response = self.client.get(self._url("off"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_enqueue.call_count, 1)

    @mock.patch("pdu_manager.views.JobResult.enqueue_job")
    def test_invalid_action_does_not_enqueue(self, mock_enqueue):
        self.add_permissions("extras.run_job", "pdu_manager.view_pduoutletstatus")
        response = self.client.get(self._url("frobnicate"))
        self.assertEqual(response.status_code, 302)
        mock_enqueue.assert_not_called()

    @mock.patch("pdu_manager.views.JobResult.enqueue_job")
    def test_protected_device_is_refused(self, mock_enqueue):
        # The server downstream of the outlet is protected, so Off must be refused.
        fixtures.create_power_off_protection("protect-server", devices=[self.env["server"]])
        self.add_permissions("extras.run_job", "pdu_manager.view_pduoutletstatus")
        response = self.client.get(self._url("off"))
        self.assertEqual(response.status_code, 302)
        mock_enqueue.assert_not_called()
