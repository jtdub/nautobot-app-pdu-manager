"""Template extensions for pdu_manager.

Adds a "PDU Power" button to every device detail page. The button links to a control view
that works for both an APC PDU (per-outlet controls) and a device powered by a PDU outlet
(controls for its feeding outlet). The view itself handles devices with no PDU relationship.
"""

from nautobot.apps.ui import Button, ButtonColorChoices, TemplateExtension


class DevicePowerControl(TemplateExtension):  # pylint: disable=abstract-method
    """Add a PDU power-control button to the device detail page.

    Only the declarative ``object_detail_buttons`` hook is needed; the other
    TemplateExtension hooks keep their no-op base implementations.
    """

    model = "dcim.device"

    object_detail_buttons = (
        Button(
            weight=100,
            label="PDU Power",
            color=ButtonColorChoices.BLUE,
            icon="mdi-power-plug",
            link_name="plugins:pdu_manager:device_power_control",
            required_permissions=["extras.run_job"],
        ),
    )


template_extensions = [DevicePowerControl]
