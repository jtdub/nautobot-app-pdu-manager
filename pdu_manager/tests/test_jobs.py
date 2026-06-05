"""Tests for the PowerControlJob (SSH play is mocked)."""

from unittest import mock

from django.test import TestCase

from pdu_manager.jobs import PowerControlJob
from pdu_manager.tests import fixtures


class PowerControlJobTestCase(TestCase):
    """Verify the Job resolves the target PDU/outlet and delegates to the play."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def _job(self):
        job = PowerControlJob()
        job.logger = mock.MagicMock()
        return job

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_on_action_from_downstream_device(self, mock_run):
        job = self._job()
        job.run(device=self.env["server"], action="on")
        mock_run.assert_called_once_with(job, self.env["pdu"], "on", [5])

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_reboot_action_from_pdu_with_outlet(self, mock_run):
        job = self._job()
        job.run(device=self.env["pdu"], action="reboot", power_outlet=self.env["outlet"])
        mock_run.assert_called_once_with(job, self.env["pdu"], "reboot", [5])

    @mock.patch("pdu_manager.jobs.power_control.run_status")
    def test_status_action_from_pdu(self, mock_status):
        job = self._job()
        job.run(device=self.env["pdu"], action="status")
        mock_status.assert_called_once_with(job, self.env["pdu"])

    @mock.patch("pdu_manager.jobs.power_control.run_status")
    def test_status_action_from_downstream_resolves_pdu(self, mock_status):
        job = self._job()
        job.run(device=self.env["server"], action="status")
        mock_status.assert_called_once_with(job, self.env["pdu"])
