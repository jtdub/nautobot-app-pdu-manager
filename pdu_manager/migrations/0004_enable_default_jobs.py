"""Data migration that registers and enables the pdu_manager jobs by default.

App jobs default to ``enabled=False``; without this the built-in PDU Power dropdown items
(and the control page) would be unable to run. Kept separate from the schema migrations.
Mirrors nautobot-app-tools' approach.
"""

from django.db import migrations
from nautobot.extras.utils import refresh_job_model_from_job_class

from pdu_manager.jobs import (
    PowerControlJob,
    PowerOffJob,
    PowerOnJob,
    PowerRebootJob,
    PowerStatusJob,
)


def enable_pdu_manager_jobs(apps, schema_editor):  # pylint: disable=unused-argument
    """Create or update the Job records for all pdu_manager jobs and enable them."""
    job_model_class = apps.get_model("extras", "Job")
    job_queue_class = apps.get_model("extras", "JobQueue")

    for job_class in (PowerControlJob, PowerStatusJob, PowerOnJob, PowerOffJob, PowerRebootJob):
        job_model, _ = refresh_job_model_from_job_class(
            job_model_class=job_model_class,
            job_class=job_class,
            job_queue_class=job_queue_class,
        )
        if job_model is not None:
            job_model.enabled = True
            job_model.save()


class Migration(migrations.Migration):
    """Enable the pdu_manager jobs so the built-in buttons can run them."""

    dependencies = [
        ("pdu_manager", "0003_seed_apc_command_set"),
    ]

    operations = [
        migrations.RunPython(
            code=enable_pdu_manager_jobs,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
