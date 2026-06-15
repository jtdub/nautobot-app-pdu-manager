"""Constants for the pdu_manager app."""

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

# Actions that remove power from a device (Reboot power-cycles, so it briefly powers off).
# These are refused when a device matches an enabled PowerOffProtection rule.
PROTECTED_ACTIONS = (ACTION_OFF, ACTION_REBOOT)

# Stored outlet states for the PduOutletStatus model. A Status run normalizes the parsed
# CLI state ("On"/"Off") to STATE_ON/STATE_OFF; anything else (or a never-polled outlet) is
# STATE_UNKNOWN. The device-page panel renders On green, Off red, and Unknown grey.
STATE_ON = "On"
STATE_OFF = "Off"
STATE_UNKNOWN = "Unknown"

STATE_CHOICES = (
    (STATE_ON, "On"),
    (STATE_OFF, "Off"),
    (STATE_UNKNOWN, "Unknown"),
)

# The stored outlet state that results from a successful power action (a reboot ends
# powered on). Used to update PduOutletStatus immediately after an action succeeds.
ACTION_TO_STATE = {
    ACTION_ON: STATE_ON,
    ACTION_OFF: STATE_OFF,
    ACTION_REBOOT: STATE_ON,
}

# Default PduCommandSet field values for APC Network Management Card (AOS) PDUs. Seeded by
# the 0003_seed_apc_command_set data migration and assigned to the APC platform by the
# generate_pdu_manager_test_data command. Editable per-platform via the PduCommandSet UI/API.
APC_DEFAULT_COMMAND_SET = {
    "name": "APC AOS",
    "description": "APC Network Management Card (AOS) outlet-control CLI commands.",
    "on_command": "olOn",
    "off_command": "olOff",
    "reboot_command": "olReboot",
    "status_command": "olStatus",
    "status_all_argument": "all",
    "outlet_separator": ",",
    "success_string": "E000",
    "status_parse_regex": r"^\s*(?P<id>\d+):\s*(?P<name>.*?):\s*(?P<state>On|Off)\s*$",
}
