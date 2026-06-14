"""Management command that populates Nautobot with PDU Manager demo/test data.

Modeled on nautobot-app-operational-compliance's ``generate_..._test_data`` command. It is
idempotent (everything uses ``get_or_create``) so it can be re-run safely, and ``--flush``
clears the app-owned ``PowerOffProtection`` rules first. It builds, per site:

* an APC PDU (``apc_aos`` platform) with 8 named outlets and an assigned Secrets Group,
* four downstream devices cabled to outlets (a core switch, two servers, an access switch),

then creates Power Off Protection rules exercising every match type (role / tenant / tag /
explicit device, plus a disabled rule). Combined with ``MOCK_CONNECTIONS`` it lets you drive
the whole UI -- the per-device PDU dropdown, the PDU control page, protection enforcement,
and the running jobs -- without any real APC hardware.
"""

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from nautobot.apps.choices import ColorChoices
from nautobot.dcim.models import (
    Cable,
    Device,
    DeviceType,
    Location,
    LocationType,
    Manufacturer,
    Platform,
    PowerOutlet,
    PowerPort,
)
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
from nautobot.extras.models import Job, JobQueue, Role, Secret, SecretsGroup, SecretsGroupAssociation, Status, Tag
from nautobot.extras.utils import refresh_job_model_from_job_class
from nautobot.tenancy.models import Tenant

from pdu_manager.constants import APC_DEFAULT_COMMAND_SET, APC_NETWORK_DRIVER
from pdu_manager.jobs import (
    PowerControlJob,
    PowerOffJob,
    PowerOnJob,
    PowerRebootJob,
    PowerStatusJob,
)
from pdu_manager.models import PduCommandSet, PowerOffProtection

# Jobs to register and enable so the device-page PDU Power dropdown can run them.
PDU_JOB_CLASSES = (PowerControlJob, PowerStatusJob, PowerOnJob, PowerOffJob, PowerRebootJob)

OUTLETS_PER_PDU = 8

# Roles to create: name -> color.
ROLES = {
    "PDU": ColorChoices.COLOR_TEAL,
    "Core Switch": ColorChoices.COLOR_RED,
    "Server": ColorChoices.COLOR_BLUE,
    "Access Switch": ColorChoices.COLOR_GREEN,
}

# Sites: display name -> device-name prefix.
SITES = {"DC-East": "dce", "DC-West": "dcw"}

# Downstream devices per site: (suffix, role, device_type, tenant, tags, outlet_number).
DOWNSTREAM = [
    ("core-01", "Core Switch", "QFX5120-48Y", "Production", [], 1),
    ("srv-01", "Server", "PowerEdge R740", "Production", [], 2),
    ("srv-02", "Server", "PowerEdge R740", None, ["critical"], 3),
    ("acc-01", "Access Switch", "QFX5120-48Y", None, [], 4),
]


class Command(BaseCommand):
    """Populate the database with sample PDU Manager data for demos and UI testing."""

    help = "Generate PDU Manager demo data (PDUs, outlets, cabled devices, protection rules)."

    def add_arguments(self, parser):
        """Register the --database and --flush command-line options."""
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='The database to generate the test data in. Defaults to the "default" database.',
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing Power Off Protection rules before generating new data.",
        )

    def handle(self, *args, **options):
        """Build the demo data set."""
        using = options["database"]

        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing PowerOffProtection rules..."))
            PowerOffProtection.objects.using(using).all().delete()

        infra = self._ensure_infrastructure()
        self._ensure_tenants_and_tags()
        for site_name, prefix in SITES.items():
            self._ensure_site(site_name, prefix, infra)
        self._ensure_protections(infra)
        self._enable_jobs()

        self.stdout.write(self.style.SUCCESS("Successfully populated PDU Manager demo data."))
        pdu_count = Device.objects.filter(role__name="PDU").count()
        self.stdout.write(
            f"  Devices: {Device.objects.count()} | PDUs: {pdu_count} | "
            f"Outlets: {PowerOutlet.objects.count()} | Protection rules: {PowerOffProtection.objects.count()}"
        )
        self.stdout.write(
            "  Enable PLUGINS_CONFIG['pdu_manager']['MOCK_CONNECTIONS'] = True to run the jobs without real PDUs."
        )

    def _enable_jobs(self):
        """Register and enable the pdu_manager jobs so the device-page buttons can run them.

        App jobs default to ``enabled=False``; a disabled job's run form (the modal opened by
        the dropdown) is not interactive, so enabling them here makes the demo work end-to-end
        even if the enabling migration has not run.
        """
        enabled = 0
        for job_class in PDU_JOB_CLASSES:
            job_model, _ = refresh_job_model_from_job_class(
                job_model_class=Job,
                job_class=job_class,
                job_queue_class=JobQueue,
            )
            if job_model is not None and not job_model.enabled:
                job_model.enabled = True
                job_model.save()
                enabled += 1
        self.stdout.write(f"  Enabled PDU Manager jobs ({enabled} newly enabled).")

    # -- infrastructure -------------------------------------------------------------------

    def _ensure_infrastructure(self):  # pylint: disable=too-many-locals
        """Create manufacturers, device types, platform, roles, location, and statuses."""
        apc, _ = Manufacturer.objects.get_or_create(name="APC")
        dell, _ = Manufacturer.objects.get_or_create(name="Dell")
        juniper, _ = Manufacturer.objects.get_or_create(name="Juniper")

        device_types = {}
        for model, mfr in [("AP8841", apc), ("PowerEdge R740", dell), ("QFX5120-48Y", juniper)]:
            device_types[model], _ = DeviceType.objects.get_or_create(model=model, defaults={"manufacturer": mfr})

        platform, _ = Platform.objects.get_or_create(
            name="APC AOS", defaults={"manufacturer": apc, "network_driver": APC_NETWORK_DRIVER}
        )
        # Assign the APC command set (created by the app's signal) to the APC platform.
        command_set, _ = PduCommandSet.objects.get_or_create(
            name=APC_DEFAULT_COMMAND_SET["name"],
            defaults={key: value for key, value in APC_DEFAULT_COMMAND_SET.items() if key != "name"},
        )
        command_set.platforms.add(platform)

        device_ct = ContentType.objects.get_for_model(Device)
        roles = {}
        for name, color in ROLES.items():
            role, created = Role.objects.get_or_create(name=name, defaults={"color": color})
            if created:
                role.content_types.add(device_ct)
            roles[name] = role

        site_type, _ = LocationType.objects.get_or_create(name="Site")
        site_type.content_types.add(device_ct)

        return {
            "device_types": device_types,
            "platform": platform,
            "roles": roles,
            "site_type": site_type,
            "device_status": Status.objects.get_for_model(Device).first(),
            "location_status": Status.objects.get_for_model(Location).first(),
            "cable_status": Status.objects.get_for_model(Cable).first(),
            "secrets_group": self._ensure_secrets_group(),
        }

    def _ensure_secrets_group(self):
        """Create a Secrets Group with env-var username/password for the PDUs."""
        username, _ = Secret.objects.get_or_create(
            name="APC PDU Username",
            defaults={"provider": "environment-variable", "parameters": {"variable": "PDU_USERNAME"}},
        )
        password, _ = Secret.objects.get_or_create(
            name="APC PDU Password",
            defaults={"provider": "environment-variable", "parameters": {"variable": "PDU_PASSWORD"}},
        )
        group, _ = SecretsGroup.objects.get_or_create(name="APC PDU Credentials")
        for secret, secret_type in [
            (username, SecretsGroupSecretTypeChoices.TYPE_USERNAME),
            (password, SecretsGroupSecretTypeChoices.TYPE_PASSWORD),
        ]:
            SecretsGroupAssociation.objects.get_or_create(
                secrets_group=group,
                access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
                secret_type=secret_type,
                defaults={"secret": secret},
            )
        return group

    def _ensure_tenants_and_tags(self):
        """Create the tenants and tags the protection rules match on."""
        for name in ("Production", "Lab"):
            Tenant.objects.get_or_create(name=name)
        tag, created = Tag.objects.get_or_create(name="critical", defaults={"color": ColorChoices.COLOR_RED})
        if created:
            tag.content_types.add(ContentType.objects.get_for_model(Device))

    def _ensure_site(self, site_name, prefix, infra):  # pylint: disable=too-many-locals
        """Create one site's PDU, outlets, downstream devices, and cabling."""
        location, _ = Location.objects.get_or_create(
            name=site_name, location_type=infra["site_type"], defaults={"status": infra["location_status"]}
        )

        pdu = self._ensure_device(
            name=f"{prefix}-pdu-01",
            role="PDU",
            device_type="AP8841",
            location=location,
            infra=infra,
            platform=infra["platform"],
            secrets_group=infra["secrets_group"],
        )
        outlets = {}
        for number in range(1, OUTLETS_PER_PDU + 1):
            outlet, _ = PowerOutlet.objects.get_or_create(device=pdu, name=f"Outlet {number}")
            outlets[number] = outlet

        for suffix, role, device_type, tenant_name, tag_names, outlet_number in DOWNSTREAM:
            device = self._ensure_device(
                name=f"{prefix}-{suffix}",
                role=role,
                device_type=device_type,
                location=location,
                infra=infra,
                tenant_name=tenant_name,
                tag_names=tag_names,
            )
            self._ensure_cabling(device, outlets[outlet_number], infra["cable_status"])

    def _ensure_device(  # pylint: disable=too-many-arguments
        self,
        *,
        name,
        role,
        device_type,
        location,
        infra,
        platform=None,
        secrets_group=None,
        tenant_name=None,
        tag_names=None,
    ):
        """Create (idempotently) a device and apply its tenant/tags/secrets group."""
        device, _ = Device.objects.get_or_create(
            name=name,
            defaults={
                "role": infra["roles"][role],
                "device_type": infra["device_types"][device_type],
                "location": location,
                "status": infra["device_status"],
            },
        )
        changed = False
        if platform is not None and device.platform_id != platform.pk:
            device.platform = platform
            changed = True
        if secrets_group is not None and device.secrets_group_id != secrets_group.pk:
            device.secrets_group = secrets_group
            changed = True
        if tenant_name:
            device.tenant = Tenant.objects.get(name=tenant_name)
            changed = True
        if changed:
            device.validated_save()
        for tag_name in tag_names or []:
            device.tags.add(Tag.objects.get(name=tag_name))
        return device

    def _ensure_cabling(self, device, outlet, cable_status):
        """Cable ``device``'s PSU1 power port to ``outlet`` if not already connected."""
        power_port, _ = PowerPort.objects.get_or_create(device=device, name="PSU1")
        power_port.refresh_from_db()
        if power_port.cable is None and outlet.cable is None:
            Cable(termination_a=power_port, termination_b=outlet, status=cable_status).validated_save()

    # -- protection rules -----------------------------------------------------------------

    def _ensure_protections(self, infra):
        """Create Power Off Protection rules covering every match type."""
        rules = [
            ("Protect Core Switches", {"roles": [infra["roles"]["Core Switch"]]}, True),
            ("Protect Production Tenant", {"tenants": [Tenant.objects.get(name="Production")]}, True),
            ("Protect Critical-Tagged Devices", {"device_tags": [Tag.objects.get(name="critical")]}, True),
            ("Lab Maintenance (disabled)", {"tenants": [Tenant.objects.get(name="Lab")]}, False),
        ]
        # Explicit-device rule targets the first access switch, if present.
        explicit = Device.objects.filter(name__endswith="acc-01").order_by("name").first()
        if explicit is not None:
            rules.append((f"Protect {explicit.name}", {"devices": [explicit]}, True))

        for name, criteria, enabled in rules:
            rule, _ = PowerOffProtection.objects.get_or_create(name=name, defaults={"enabled": enabled})
            for field, values in criteria.items():
                getattr(rule, field).set(values)
