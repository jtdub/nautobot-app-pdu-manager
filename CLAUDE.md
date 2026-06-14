# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`pdu_manager` is a Nautobot 3.x app (plugin) that controls **APC PDU outlets over SSH**. It lets a user power an outlet on/off, reboot it, or read outlet status — either from the PDU device itself or from any device that is powered by a PDU outlet. It was scaffolded from the Network to Code `nautobot-app` cookiecutter, so a lot of the surrounding files (the `PduManager` ORM model, its viewset/forms/tables/serializers/filters, the README boilerplate) are stock template artifacts. **The actual feature lives in the power-control path**, not in the `PduManager` model.

## Development environment & commands

Everything runs through `invoke` against a `docker-compose` stack (Nautobot + Postgres/MySQL + Redis). Tasks are defined in `tasks.py`; config is in `invoke.yml` (Nautobot/Python versions). You do **not** run Python or Django directly on the host.

```bash
invoke build            # build the dev containers
invoke start            # start the stack (Nautobot at :8080, docs at :8001)
invoke stop             # stop; invoke destroy wipes volumes
invoke createsuperuser  # bootstrap an admin user
invoke nbshell          # Nautobot Django shell; invoke cli opens a bash shell in the container
invoke migrate / invoke makemigrations --name <n>
invoke generate-test-data           # populate demo PDUs/outlets/cabled devices/protection rules
invoke generate-test-data --flush   # wipe Power Off Protection rules first, then regenerate
```

For a hardware-free demo, set `PDU_MANAGER_MOCK_CONNECTIONS=True` (read by `development/nautobot_config.py` into `PLUGINS_CONFIG["pdu_manager"]["MOCK_CONNECTIONS"]`) and run `invoke generate-test-data`. The power-control jobs then simulate the APC CLI instead of opening SSH, so the whole UI (per-device PDU dropdown, control page, protection enforcement, JobResult logs) works end-to-end.

Tests and linting (all execute inside the Nautobot container):

```bash
invoke unittest                                  # full suite; builds docs first
invoke unittest --skip-docs-build                # skip the docs build step (faster)
invoke unittest --pattern test_resolve_pdu       # single test/class/module (passed to -k)
invoke unittest --label pdu_manager.tests.test_jobs   # narrow to one module
invoke unittest --keepdb --failfast              # reuse the test DB, stop on first failure
invoke unittest --coverage                       # then: invoke unittest-coverage
invoke tests                                     # lint + unit tests (what CI runs)
invoke tests --lint-only                         # linters only, no unit tests
```

Linters are also individual tasks: `invoke ruff` / `invoke ruff --fix`, `invoke pylint`, `invoke djlint`, `invoke djhtml`, `invoke yamllint`, `invoke markdownlint`, `invoke autoformat` (alias `invoke a`). Ruff config (line-length 120, google docstrings, bandit) and pylint config live in `pyproject.toml`.

## Architecture of the power-control feature

The flow is **UI button → control page → job-enqueue view → Nautobot Job → Nornir play → netmiko/APC CLI**. Trace it through these files:

- **`template_content.py`** — `DevicePowerControl` adds a built-in "PDU Power" dropdown (On/Off/Reboot/Status, Material Design `mdi-power` icon) to *every* `dcim.device` detail page via the **declarative `object_detail_buttons`** API (a `DropdownButton` whose children are `_JobModalButton`s). Each item launches the matching per-action Job in a modal with the device pre-filled, so no Nautobot JobButton has to be configured. NOTE: Nautobot 3.x is **Bootstrap 5 + MDI**; the legacy `buttons()` hook does *not* render on the component-based device detail page, and Bootstrap-3 markup (`glyphicon`, `data-toggle`, `panel`) is broken — use the UI-framework components. Pattern mirrors `nautobot-app-tools`; `_JobModalButton` is an experimental Nautobot API.
- **`views.py`** — `DevicePowerControlView` (GET) renders the per-outlet control page; `DevicePowerActionView` (POST) enqueues `PowerControlJob`. Still reachable by URL (`devices/<uuid:pk>/power/`) but secondary to the dropdown; its templates still use Bootstrap-3 markup pending a BS5 pass. Also hosts `PowerOffProtectionUIViewSet`.
- **`jobs.py`** — `_BasePduJob` holds the shared resolve/protection/delegate logic; `PowerControlJob` (device + outlet + action choice) backs the control page, and `PowerStatusJob`/`PowerOnJob`/`PowerOffJob`/`PowerRebootJob` (one fixed action each) back the dropdown items. Expected errors (protected device, no PDU, unparseable outlet) are reported via `self.fail()` as a clean Job **Failure** log entry, not a traceback. Status is **scoped** to the device's outlet(s) (`olStatus 5`), not the whole PDU.
- **`utils.py`** — resolution logic. A device is treated as a PDU if it has `power_outlets`. A downstream device is mapped to its feeding outlet by walking its `power_ports` to the connected `PowerOutlet` endpoint. The APC CLI outlet number is **parsed from the trailing integer of the outlet's name** (`outlet_index`, e.g. `"Power Outlet 17"` → `17`); a name with no trailing integer is uncontrollable (`resolve_pdu_and_outlets` raises). This module also holds the **Power Off Protection** matching/guard helpers (`power_off_protections_for`, `is_power_off_protected`, `blocked_protected_devices`, `downstream_devices_for_outlet`).
- **`nornir_plays/power_control.py`** — resolves the target PDU's **`PduCommandSet`** (via `utils.command_set_for`, by Platform), builds the CLI command from it, runs it through Nornir using the **NautobotORMInventory** (`nautobot-plugin-nornir`) scoped to the single PDU device with `netmiko_send_command`, and verifies success via `command_set.check_success`. There are **no hard-coded verbs/codes** here anymore. The single choke point `_run()` short-circuits to the mock when `MOCK_CONNECTIONS` is on.
- **`config.py`** — `mock_connections_enabled()` reads `PLUGINS_CONFIG["pdu_manager"]["MOCK_CONNECTIONS"]` (default False, declared in `__init__.py` `default_settings`).
- **`nornir_plays/mock.py`** — `simulate_command(pdu, command, command_set)` returns canned CLI output (using the command set's verbs/success string) and tracks per-outlet on/off state in the Django cache, so a status query reflects prior on/off/reboot actions within a demo session.
- **`management/commands/generate_pdu_manager_test_data.py`** — idempotent demo-data generator (run via `invoke generate-test-data`): per-site APC PDUs with 8 named outlets + Secrets Group, downstream devices cabled to outlets, and Power Off Protection rules exercising every match type. `--flush` clears only the app-owned `PowerOffProtection` rules.
- **`nornir_plays/processor.py`** (`ProcessPdu`) and **`nornir_plays/logger.py`** (`NornirLogger`) bridge Nornir results back into the Nautobot JobResult log.
- **`constants.py`** — action keys, the power-removing `PROTECTED_ACTIONS` (off/reboot), the `apc_aos` driver, and `APC_DEFAULT_COMMAND_SET` (the field values used to seed the APC `PduCommandSet`). The actual verbs/success/regex live on the model, not here.
- **`models.py` / `forms.py` / `tables.py` / `filters.py` / `navigation.py` / `api/`** — two models with full UI + REST API:
    - `PowerOffProtection` — a device is protected (Off/Reboot refused) when it matches any *enabled* rule by role, tenant, tag, or explicit device; enforced in both `PowerControlJob` and `DevicePowerActionView`.
    - `PduCommandSet` — per-`Platform` definition of the on/off/reboot/status verbs, success string, and status-parse regex. Its methods (`build_command`, `build_status_command`, `check_success`, `parse_status`) are what the play uses. The default APC set is seeded by the `0003_seed_apc_command_set` **data** migration; `generate-test-data` and the test fixtures assign it to the APC platform. To support a new PDU vendor, add a `PduCommandSet` (UI/API) and assign its platform — **no code change**.

  **Migrations are split by purpose**: schema migrations contain only `CreateModel` (`0001_initial`, `0002_pducommandset`); data migrations contain only `RunPython` (`0003_seed_apc_command_set`, `0004_enable_default_jobs`). Keep that separation — never mix `CreateModel`/`AddField` with `RunPython` in one file. Note this environment's `makemigrations` **omits `help_text`** and orders kwargs/M2M alphabetically, so hand-written schema migrations must match that to pass `invoke tests`' `makemigrations --check`.

### Infrastructure dependency that must hold

**Credentials & inventory come from `nautobot-plugin-nornir`** (`NORNIR_SETTINGS`), which is pinned to a **git `develop` branch** in `pyproject.toml` because PyPI releases don't yet support Nautobot 3.x. APC PDU devices must have their Platform `network_driver` set to `apc_aos` and have Secrets-based credentials configured for the ORM inventory.

> Outlet numbering needs **no setup**: the APC outlet number is derived from the trailing integer of the Nautobot outlet name (so name outlets like `"Power Outlet 5"`). There is no longer a `pdu_outlet_id` CustomField or `nautobot_database_ready` signal.

### Lazy ORM imports

Several modules (`utils.py`, `power_control.py`) import `nautobot.dcim`/app models **inside functions**, not at module top level, so the modules can be imported before the Django app registry is ready. Preserve this pattern when editing them.

## Conventions

- **Changelog fragments are required** on every PR. Add a file in `changes/` named `<issue#>.<type>` (types: `added`, `changed`, `deprecated`, `fixed`, `removed`, `security`, etc.), one complete past-tense sentence per line. Release notes are assembled with towncrier (`invoke generate-release-notes`).
- **Branch from `develop`** for features (PRs target `develop`/`next`); LTM fixes branch from `ltm-<major.minor>`.
- Tests use Nautobot's base test cases and live in `pdu_manager/tests/` (one `test_*.py` per module). Migrations and tests are exempt from docstring/bandit lint rules (see `pyproject.toml` per-file-ignores).
