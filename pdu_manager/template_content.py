"""Template extensions for pdu_manager.

Adds a built-in "PDU Power" dropdown (On / Off / Reboot / Status) to every ``dcim.device``
detail page. Each item launches the matching per-action Job in a modal with the device
pre-filled, so no Nautobot JobButton has to be configured by hand. This uses the declarative
``object_detail_buttons`` UI-framework API (a native Bootstrap-5 dropdown with a Material
Design power icon) rather than the legacy ``buttons()`` hook, which does not render on
Nautobot 3.x's component-based device detail page. Pattern mirrors nautobot-app-tools.
"""

from nautobot.apps.ui import (
    ButtonColorChoices,
    DropdownButton,
    ObjectsTablePanel,
    SectionChoices,
    Tab,
    TemplateExtension,
)
from nautobot.core.ui.object_detail import _JobModalButton

from pdu_manager.tables import PduOutletStatusTable

# Pre-fill each Job's `device` ObjectVar from the device whose page the button is on.
_DEVICE_MAPPING = {"device": "id"}


class DevicePowerControl(TemplateExtension):  # pylint: disable=abstract-method
    """Add a built-in PDU power dropdown to the device detail page."""

    model = "dcim.device"

    object_detail_buttons = [
        DropdownButton(
            label="PDU Power",
            icon="mdi-power",
            color=ButtonColorChoices.BLUE,
            weight=100,
            required_permissions=["extras.run_job"],
            children=[
                _JobModalButton(
                    label="Status",
                    icon="mdi-information-outline",
                    weight=100,
                    class_path="pdu_manager.jobs.PowerStatusJob",
                    initial_field_mapping=_DEVICE_MAPPING,
                ),
                _JobModalButton(
                    label="On",
                    icon="mdi-power-plug",
                    color=ButtonColorChoices.GREEN,
                    weight=200,
                    class_path="pdu_manager.jobs.PowerOnJob",
                    initial_field_mapping=_DEVICE_MAPPING,
                ),
                _JobModalButton(
                    label="Off",
                    icon="mdi-power-plug-off",
                    color=ButtonColorChoices.RED,
                    weight=300,
                    class_path="pdu_manager.jobs.PowerOffJob",
                    initial_field_mapping=_DEVICE_MAPPING,
                ),
                _JobModalButton(
                    label="Reboot",
                    icon="mdi-restart",
                    color=ButtonColorChoices.YELLOW,
                    weight=400,
                    class_path="pdu_manager.jobs.PowerRebootJob",
                    initial_field_mapping=_DEVICE_MAPPING,
                ),
            ],
        ),
    ]

    # Show the stored per-outlet status (On green / Off red) in a dedicated "PDU Status" tab
    # on the device detail page. The table is empty for devices with no outlets; a Status run
    # (the dropdown's "Status" item, which launches PowerStatusJob) populates it.
    # ``table_filter="device"`` scopes the table to this device's PduOutletStatus rows.
    object_detail_tabs = [
        Tab(
            weight=1000,
            tab_id="pdu_outlet_status",
            label="PDU Status",
            panels=[
                ObjectsTablePanel(
                    weight=100,
                    section=SectionChoices.FULL_WIDTH,
                    label="PDU Outlet Status",
                    table_class=PduOutletStatusTable,
                    table_filter="device",
                    select_related_fields=["device", "power_outlet"],
                    add_button_route=None,
                    exclude_columns=["pk", "device", "actions"],
                ),
            ],
        ),
    ]


template_extensions = [DevicePowerControl]
