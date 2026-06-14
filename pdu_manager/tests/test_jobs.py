"""Tests for the PDU power jobs (SSH play is mocked)."""

from unittest import mock

from django.test import TestCase

from pdu_manager.jobs import (
    PowerControlJob,
    PowerOffJob,
    PowerOnJob,
    PowerRebootJob,
    PowerStatusJob,
)
from pdu_manager.tests import fixtures


class PowerControlJobTestCase(TestCase):
    """Verify PowerControlJob resolves the target PDU/outlet and delegates to the play."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def _job(self, job_class=PowerControlJob):
        job = job_class()
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
    def test_status_from_pdu_reports_all_outlets(self, mock_status):
        job = self._job()
        job.run(device=self.env["pdu"], action="status")
        mock_status.assert_called_once_with(job, self.env["pdu"])

    @mock.patch("pdu_manager.jobs.power_control.run_status")
    def test_status_from_downstream_is_scoped_to_its_outlet(self, mock_status):
        job = self._job()
        job.run(device=self.env["server"], action="status")
        mock_status.assert_called_once_with(job, self.env["pdu"], [5])

    @mock.patch("pdu_manager.jobs.power_control.run_status")
    def test_status_from_pdu_with_outlet_is_scoped(self, mock_status):
        job = self._job()
        job.run(device=self.env["pdu"], action="status", power_outlet=self.env["outlet"])
        mock_status.assert_called_once_with(job, self.env["pdu"], [5])

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_off_refused_for_protected_device_logs_failure(self, mock_run):
        fixtures.create_power_off_protection("protect-server", devices=[self.env["server"]])
        job = self._job()
        job.run(device=self.env["server"], action="off")
        self.assertTrue(job._failed)  # pylint: disable=protected-access
        mock_run.assert_not_called()

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_off_allowed_when_unprotected(self, mock_run):
        job = self._job()
        job.run(device=self.env["server"], action="off")
        mock_run.assert_called_once_with(job, self.env["pdu"], "off", [5])

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_unresolvable_target_logs_failure(self, mock_run):
        self.env["power_port"].cable.delete()  # server no longer fed by an outlet
        job = self._job()
        job.run(device=self.env["server"], action="on")
        self.assertTrue(job._failed)  # pylint: disable=protected-access
        mock_run.assert_not_called()


class SingleActionJobsTestCase(TestCase):
    """Verify the per-action dropdown jobs run their fixed action."""

    @classmethod
    def setUpTestData(cls):
        cls.env = fixtures.create_pdu_environment()

    def _job(self, job_class):
        job = job_class()
        job.logger = mock.MagicMock()
        return job

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_power_on_job(self, mock_run):
        job = self._job(PowerOnJob)
        job.run(device=self.env["server"])
        mock_run.assert_called_once_with(job, self.env["pdu"], "on", [5])

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_power_off_job(self, mock_run):
        job = self._job(PowerOffJob)
        job.run(device=self.env["server"])
        mock_run.assert_called_once_with(job, self.env["pdu"], "off", [5])

    @mock.patch("pdu_manager.jobs.power_control.run_power_action")
    def test_power_reboot_job(self, mock_run):
        job = self._job(PowerRebootJob)
        job.run(device=self.env["server"])
        mock_run.assert_called_once_with(job, self.env["pdu"], "reboot", [5])

    @mock.patch("pdu_manager.jobs.power_control.run_status")
    def test_power_status_job_is_scoped(self, mock_status):
        job = self._job(PowerStatusJob)
        job.run(device=self.env["server"])
        mock_status.assert_called_once_with(job, self.env["pdu"], [5])
