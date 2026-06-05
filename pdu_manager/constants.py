"""Constants for the pdu_manager app."""

# CustomField key on dcim.PowerOutlet that stores the numeric outlet index the APC CLI
# uses (e.g. the "5" in `olOn 5`). Keep in sync with signals.create_pdu_outlet_custom_field.
PDU_OUTLET_ID_FIELD = "pdu_outlet_id"

# The netmiko/Nautobot Platform network_driver expected on APC PDU devices.
APC_NETWORK_DRIVER = "apc_aos"

# Supported power actions and the APC CLI verb each maps to.
ACTION_ON = "on"
ACTION_OFF = "off"
ACTION_REBOOT = "reboot"
ACTION_STATUS = "status"

ACTION_CHOICES = (
    (ACTION_ON, "On"),
    (ACTION_OFF, "Off"),
    (ACTION_REBOOT, "Reboot"),
    (ACTION_STATUS, "Status"),
)

# Map an action to its APC CLI command verb. `status` is handled separately (olStatus all).
ACTION_COMMANDS = {
    ACTION_ON: "olOn",
    ACTION_OFF: "olOff",
    ACTION_REBOOT: "olReboot",
}

# APC NMC returns this code on a successful outlet command.
APC_SUCCESS_CODE = "E000"
