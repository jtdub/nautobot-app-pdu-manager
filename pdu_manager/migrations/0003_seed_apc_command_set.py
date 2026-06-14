"""Data migration that seeds the default APC PduCommandSet (no Platform assigned).

Kept separate from the schema migration that creates the model. Assign a Platform to the
set in the UI/API (or run ``invoke generate-test-data``) to put it into use.
"""

from django.db import migrations

from pdu_manager.constants import APC_DEFAULT_COMMAND_SET


def create_apc_command_set(apps, schema_editor):  # pylint: disable=unused-argument
    """Create the default APC command set if it does not already exist."""
    pdu_command_set = apps.get_model("pdu_manager", "PduCommandSet")
    pdu_command_set.objects.get_or_create(
        name=APC_DEFAULT_COMMAND_SET["name"],
        defaults={key: value for key, value in APC_DEFAULT_COMMAND_SET.items() if key != "name"},
    )


def delete_apc_command_set(apps, schema_editor):  # pylint: disable=unused-argument
    """Remove the default APC command set on reverse."""
    pdu_command_set = apps.get_model("pdu_manager", "PduCommandSet")
    pdu_command_set.objects.filter(name=APC_DEFAULT_COMMAND_SET["name"]).delete()


class Migration(migrations.Migration):
    """Seed the default APC command set."""

    dependencies = [
        ("pdu_manager", "0002_pducommandset"),
    ]

    operations = [
        migrations.RunPython(code=create_apc_command_set, reverse_code=delete_apc_command_set),
    ]
