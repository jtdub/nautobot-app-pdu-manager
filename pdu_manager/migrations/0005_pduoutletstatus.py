import uuid

import django.core.serializers.json
import django.db.models.deletion
import nautobot.core.models.fields
import nautobot.extras.models.mixins
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dcim", "0084_add_module_type_image_support"),
        ("extras", "0142_remove_scheduledjob_approval_required"),
        ("pdu_manager", "0004_enable_default_jobs"),
    ]

    operations = [
        migrations.CreateModel(
            name="PduOutletStatus",
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
                ("outlet_index", models.PositiveIntegerField()),
                (
                    "state",
                    models.CharField(
                        choices=[("On", "On"), ("Off", "Off"), ("Unknown", "Unknown")],
                        default="Unknown",
                        max_length=16,
                    ),
                ),
                ("last_polled", models.DateTimeField(blank=True, null=True)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pdu_outlet_statuses",
                        to="dcim.device",
                    ),
                ),
                (
                    "power_outlet",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pdu_outlet_status",
                        to="dcim.poweroutlet",
                    ),
                ),
                ("tags", nautobot.core.models.fields.TagsField(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "verbose_name": "PDU Outlet Status",
                "verbose_name_plural": "PDU Outlet Statuses",
                "ordering": ["device", "outlet_index"],
            },
            bases=(
                nautobot.extras.models.mixins.DataComplianceModelMixin,
                nautobot.extras.models.mixins.DynamicGroupMixin,
                nautobot.extras.models.mixins.NotesMixin,
                models.Model,
            ),
        ),
    ]
