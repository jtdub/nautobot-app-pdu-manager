
## [v1.0.0a1 (2026-06-14)](https://github.com/jtdub/nautobot-app-pdu-manager/releases/tag/v1.0.0a1)

### Added

- Added APC PDU outlet control over SSH: power an outlet on/off, reboot it, or read its status, driven from either the PDU device or any device powered by a PDU outlet, via a Nornir/Netmiko play using nautobot-plugin-nornir credentials and inventory.
- Added a built-in "PDU Power" dropdown (Status/On/Off/Reboot, Material Design power icon) to every device detail page using the declarative object_detail_buttons UI framework, with each item launching its action as a Job — no Nautobot JobButton configuration required.
- Added a `PowerOffProtection` model, with full UI and REST API, that prevents matched devices from being powered off or rebooted; rules match on role, tenant, tag, or explicit device, and are enforced in both the jobs and the views (including when an action targets a PDU outlet that feeds a protected device).
- Added full REST API CRUD for Power Off Protection rules under `/api/plugins/pdu-manager/power-off-protections/`.
- Added a `PduCommandSet` model (with UI and REST API) that defines a managed PDU's CLI commands (the on/off/reboot/status verbs), success string, and status-parsing regex per Platform, so additional PDU vendors can be supported without code changes; the default APC command set is created automatically and assigned to the APC platform by `generate-test-data`, and the jobs resolve a device's commands from its PDU's Platform at run time instead of using hard-coded APC commands.
- Added derivation of the APC outlet number from the trailing integer of the Nautobot power outlet's name (e.g. "Power Outlet 5" maps to APC outlet 5), so no per-outlet configuration is required.
- Added scoping of the Status action to the selected device's own outlet(s) rather than every outlet on the PDU.
- Added clean Job "Failure" log entries (via `self.fail()`) for expected problems such as a protected device, a device with no PDU outlet, or an unparseable outlet name, instead of unhandled tracebacks.
- Added a `MOCK_CONNECTIONS` app setting that simulates APC PDU SSH sessions when the power-control jobs run, returning realistic cache-backed APC CLI output so the app can be demoed without real hardware.
- Added a `generate_pdu_manager_test_data` management command (and an `invoke generate-test-data` wrapper) that populates demo PDUs, named outlets, cabled downstream devices, and Power Off Protection rules covering every match type, and enables the PDU Manager jobs, for end-to-end UI validation.
- Added a minimum Nautobot version of 3.1.0, required by the device-page PDU Power dropdown's use of the 3.1 UI job-modal button API.

# v1.0 Release Notes

!!! warning "Developer Note - Remove Me!"
    Guiding Principles:

    - Changelogs are for humans, not machines.
    - There should be an entry for every single version.
    - The same types of changes should be grouped.
    - Versions and sections should be linkable.
    - The latest version comes first.
    - The release date of each version is displayed.
    - Mention whether you follow Semantic Versioning.

    Types of changes:

    - `Added` for new features.
    - `Changed` for changes in existing functionality.
    - `Deprecated` for soon-to-be removed features.
    - `Removed` for now removed features.
    - `Fixed` for any bug fixes.
    - `Security` in case of vulnerabilities.


This document describes all new features and changes in the release `1.0`. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Major features or milestones
- Achieved in this `x.y` release
- Changes to compatibility with Nautobot and/or other apps, libraries etc.

## [v1.0.1] - 2021-09-08

### Added

### Changed

### Fixed

- [#123](https://github.com/jtdub/nautobot-app-pdu-manager/issues/123) Fixed Tag filtering not working in job launch form

## [v1.0.0] - 2021-08-03

### Added

### Changed

### Fixed
