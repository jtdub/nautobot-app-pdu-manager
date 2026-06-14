# Getting Started with the App

This document provides a step-by-step tutorial on how to get the App going and how to use it.

## Install the App

To install the App, please follow the instructions detailed in the [Installation Guide](../admin/install.md).

## First steps with the App

The fastest way to see the App in action — with no real PDU hardware — is the bundled demo
data and the `MOCK_CONNECTIONS` setting.

**Step 1 — Turn on connection mocking.** In your Nautobot configuration, enable the setting
(the development environment reads it from the `PDU_MANAGER_MOCK_CONNECTIONS` environment
variable):

```python
PLUGINS_CONFIG = {
    "pdu_manager": {"MOCK_CONNECTIONS": True},
}
```

**Step 2 — Load the demo data.** This creates two sites, each with an APC PDU (eight named
outlets) and several cabled downstream devices, plus Power Off Protection rules — and it
enables the PDU Manager jobs:

```bash
invoke generate-test-data
```

**Step 3 — Open a device and use the PDU Power dropdown.** Browse to any of the generated
devices (for example `dce-acc-01`) and open the **PDU Power** dropdown in the page header.

![PDU Power dropdown](https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/device-power-dropdown.png)

**Step 4 — Run an action.** Choose **Status** (or On / Off / Reboot). The Job opens in a
modal with the device pre-filled; click **Run Job Now**.

![PDU Power Status job modal](https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/power-job-modal.png)

**Step 5 — Review the result.** With mocking on, the action completes immediately and the
result shows the (simulated) outlet state — scoped to just the device's outlet:

![PDU Power Status job result](https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/power-job-result.png)

## What are the next steps?

- Try **Off** or **Reboot** on a protected device (e.g. `dce-core-01`) and watch the Job
  finish as a clean *Failure* — that is Power Off Protection at work.
- Manage protection rules under **Apps → PDU Manager → Power Off Protections**, or via the
  REST API at `/api/plugins/pdu-manager/power-off-protections/`.
- When you are ready to talk to real hardware, set `MOCK_CONNECTIONS` back to `False`, give
  each PDU a primary IP, an `apc_aos` platform, and a Secrets Group, and name each outlet
  with its APC outlet number (e.g. `Power Outlet 5`).

You can check out the [Use Cases](app_use_cases.md) section for more examples.
