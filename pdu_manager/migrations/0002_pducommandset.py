import uuid

import django.core.serializers.json
import nautobot.core.models.fields
import nautobot.extras.models.mixins
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dcim", "0084_add_module_type_image_support"),
        ("extras", "0142_remove_scheduledjob_approval_required"),
        ("pdu_manager", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PduCommandSet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "_custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("on_command", models.CharField(max_length=255)),
                ("off_command", models.CharField(max_length=255)),
                ("reboot_command", models.CharField(blank=True, max_length=255)),
                ("status_command", models.CharField(max_length=255)),
                ("status_all_argument", models.CharField(blank=True, default="all", max_length=255)),
                ("outlet_separator", models.CharField(default=",", max_length=8)),
                ("success_string", models.CharField(blank=True, default="E000", max_length=255)),
                ("status_parse_regex", models.CharField(blank=True, max_length=255)),
                (
                    "platforms",
                    models.ManyToManyField(blank=True, related_name="pdu_command_sets", to="dcim.platform"),
                ),
                ("tags", nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "verbose_name": "PDU Command Set",
                "verbose_name_plural": "PDU Command Sets",
                "ordering": ["name"],
            },
            bases=(
                nautobot.extras.models.mixins.DataComplianceModelMixin,
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
                models.Model,
            ),
        ),
    ]
