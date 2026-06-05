# Using the App

This document describes common use-cases and scenarios for this App.

## General Usage

PDU Manager lets you operate APC managed PDU (Network Management Card / AOS) outlets
directly from Nautobot — powering an outlet on or off, rebooting it, or reading outlet
status — using SSH driven by Nornir and Netmiko (the `apc_aos` driver).

It is built entirely on Nautobot's native power modeling: a PDU's outlets are
`PowerOutlet` components, a powered device exposes a `PowerPort`, and the relationship
between them is a power `Cable`.

## Prerequisites / setup

1. **Enable `nautobot_plugin_nornir`** alongside `pdu_manager` and configure it to read
   credentials from each device's Secrets Group:

    ```python
    PLUGINS = ["nautobot_plugin_nornir", "pdu_manager"]

    PLUGINS_CONFIG = {
        "nautobot_plugin_nornir": {
            "nornir_settings": {
                "credentials": "nautobot_plugin_nornir.plugins.credentials.nautobot_secrets.CredentialsNautobotSecrets",
                "runner": {"plugin": "threaded", "options": {"num_workers": 10}},
            },
        },
    }
    ```

2. **Model the PDU as a Device:**
    - Create a `Platform` with **Network driver** = `apc_aos` and assign it to the PDU device.
    - Give the PDU a **primary IP** (used as the SSH host).
    - Attach a **Secrets Group** to the PDU device providing SSH `Username` and `Password`
      secrets (access type *Generic/SSH*).
    - Add a `PowerOutlet` for each physical outlet.

3. **Map each outlet to its APC CLI number:** set the **PDU Outlet ID** custom field
   (`pdu_outlet_id`) on each `PowerOutlet` to the number the APC CLI uses (e.g. the `5`
   in `olOn 5`). This field is created automatically when the app is installed.

4. **Assign outlets to devices:** cable a downstream device's `PowerPort` to the PDU's
   `PowerOutlet` (Nautobot's standard power connection).

## Use-cases and common workflows

- **Toggle power from a device page:** the **PDU Power** button appears on every device
  detail page. On a PDU it lists every outlet with On / Off / Reboot controls; on a
  powered device it controls the single outlet feeding it. Each action enqueues the
  **PDU Power Control** Job and redirects to its Job Result.
- **Read outlet status on demand:** use **Refresh Outlet Status** (or run the Job with the
  *Status* action) to SSH to the PDU, run `olStatus all`, and log each outlet's state.
- **Run the Job directly:** Jobs → **PDU Power Control**, select a device (PDU or powered
  device), optionally an outlet, and an action.

## Screenshots
