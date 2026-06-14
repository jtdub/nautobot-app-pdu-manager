# External Interactions

This document describes external dependencies and prerequisites for this App to operate, including system requirements, API endpoints, interconnection or integrations to other applications or services, and similar topics.

## External System Integrations

### From the App to Other Systems

PDU Manager's only outbound integration is an **SSH session to each managed PDU**:

- When a power Job runs, the app connects to the target PDU over SSH (via `nautobot-plugin-nornir`'s ORM inventory + Nornir/Netmiko) using the device's **primary IP** as the host and the credentials from the device's assigned **Secrets Group**.
- It then sends the management commands defined for the PDU's platform (for APC, `olOn` / `olOff` / `olReboot` / `olStatus`) and checks the output for the configured success string (for APC, `E000`).
- The set of commands, success string, and status-parsing regex are configurable per `Platform` via the **PDU Command Set** model, so additional managed-PDU vendors can be supported without code changes.
- For demos and evaluation, setting `PLUGINS_CONFIG["pdu_manager"]["MOCK_CONNECTIONS"] = True` short-circuits this SSH path and returns simulated output, so no real PDU is contacted.

The PDU must therefore be reachable from the Nautobot worker over SSH, have its **Platform `network_driver`** set appropriately (`apc_aos` for APC), a **primary IP**, and a **Secrets Group** providing SSH username/password.

### From Other Systems to the App

The app is driven entirely through Nautobot (UI, Jobs, and REST API); it does not expose any non-Nautobot inbound interfaces.

## Nautobot REST API endpoints

PDU Manager adds standard Nautobot REST API endpoints under `/api/plugins/pdu-manager/`:

- `power-off-protections/` — CRUD for Power Off Protection rules.
- `pdu-command-sets/` — CRUD for per-platform PDU command definitions.

Power actions themselves are Nautobot Jobs and are run through the standard Nautobot Jobs REST API (`/api/extras/jobs/<id>/run/`).

```bash
# List Power Off Protection rules
curl -s -H "Authorization: Token $NAUTOBOT_TOKEN" \
  https://nautobot.example.com/api/plugins/pdu-manager/power-off-protections/
```
