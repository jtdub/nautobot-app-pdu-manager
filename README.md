# Pdu Manager

<!--
Developer Note - Remove Me!

The README will have certain links/images broken until the PR is merged into `develop`. Update the GitHub links with whichever branch you're using (main etc.) if different.

The logo of the project is a placeholder (docs/images/icon-pdu-manager.png) - please replace it with your app icon, making sure it's at least 200x200px and has a transparent background!

To avoid extra work and temporary links, make sure that publishing docs (or merging a PR) is done at the same time as setting up the docs site on RTD, then test everything.
-->

<p align="center">
  <img src="https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/icon-pdu-manager.png" class="logo" height="200px">
  <br>
  <a href="https://github.com/jtdub/nautobot-app-pdu-manager/actions"><img src="https://github.com/jtdub/nautobot-app-pdu-manager/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://docs.nautobot.com/projects/pdu-manager/en/latest/"><img src="https://readthedocs.org/projects/nautobot-app-pdu-manager/badge/"></a>
  <a href="https://pypi.org/project/pdu-manager/"><img src="https://img.shields.io/pypi/v/pdu-manager"></a>
  <a href="https://pypi.org/project/pdu-manager/"><img src="https://img.shields.io/pypi/dm/pdu-manager"></a>
  <br>
  An <a href="https://networktocode.com/nautobot-apps/">App</a> for <a href="https://nautobot.com/">Nautobot</a>.
</p>

## Overview

PDU Manager is a [Nautobot](https://nautobot.com/) app that controls **APC managed PDU outlets directly from Nautobot** — power an outlet on or off, reboot it, or read its status — over SSH (Nornir + Netmiko, the `apc_aos` driver). It works from either the PDU device itself or from any device that is powered by a PDU outlet, building entirely on Nautobot's native power modeling (a PDU's outlets are `PowerOutlet` components, a powered device exposes a `PowerPort`, and the two are joined by a power `Cable`). The APC outlet number is derived from the outlet's name, so there is no extra per-outlet configuration to maintain.

Every action runs as a Nautobot Job, surfaced as a built-in **PDU Power** dropdown (Status / On / Off / Reboot) on every device detail page — no Job Button configuration required. Each item opens the Job in a modal with the device pre-filled; the result, including outlet status, is written to the Job Result log. A Status read is scoped to just the outlet(s) feeding the selected device rather than the whole PDU.

To prevent accidental outages, PDU Manager adds a **Power Off Protection** model (with full UI and REST API) that refuses Off and Reboot for devices matched by role, tenant, tag, or explicit device. For demos and evaluation without real hardware, a `MOCK_CONNECTIONS` setting simulates the APC CLI, and an `invoke generate-test-data` command builds a complete sample environment (PDUs, cabled devices, and protection rules) and enables the jobs.

### Screenshots

The built-in **PDU Power** dropdown on a device detail page (Status / On / Off / Reboot, with a power icon):

![PDU Power dropdown on a device detail page](https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/device-power-dropdown.png)

Selecting an action opens the Job in a modal with the device pre-filled:

![PDU Power Status job modal](https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/power-job-modal.png)

The Job Result reports the outcome — here, a Status read scoped to just the device's outlet:

![PDU Power Status job result](https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/power-job-result.png)

The **Power Off Protection** rules that guard devices from being powered off or rebooted:

![Power Off Protections list](https://raw.githubusercontent.com/jtdub/nautobot-app-pdu-manager/develop/docs/images/power-off-protections-list.png)

More screenshots can be found in the [Using the App](https://docs.nautobot.com/projects/pdu-manager/en/latest/user/app_use_cases/) page in the documentation.

## Documentation

Full documentation for this App can be found over on the [Nautobot Docs](https://docs.nautobot.com) website:

- [User Guide](https://docs.nautobot.com/projects/pdu-manager/en/latest/user/app_overview/) - Overview, Using the App, Getting Started.
- [Administrator Guide](https://docs.nautobot.com/projects/pdu-manager/en/latest/admin/install/) - How to Install, Configure, Upgrade, or Uninstall the App.
- [Developer Guide](https://docs.nautobot.com/projects/pdu-manager/en/latest/dev/contributing/) - Extending the App, Code Reference, Contribution Guide.
- [Release Notes / Changelog](https://docs.nautobot.com/projects/pdu-manager/en/latest/admin/release_notes/).
- [Frequently Asked Questions](https://docs.nautobot.com/projects/pdu-manager/en/latest/user/faq/).

### Contributing to the Documentation

You can find all the Markdown source for the App documentation under the [`docs`](https://github.com/jtdub/nautobot-app-pdu-manager/tree/develop/docs) folder in this repository. For simple edits, a Markdown capable editor is sufficient: clone the repository and edit away.

If you need to view the fully-generated documentation site, you can build it with [MkDocs](https://www.mkdocs.org/). A container hosting the documentation can be started using the `invoke` commands (details in the [Development Environment Guide](https://docs.nautobot.com/projects/pdu-manager/en/latest/dev/dev_environment/#docker-development-environment)) on [http://localhost:8001](http://localhost:8001). Using this container, as your changes to the documentation are saved, they will be automatically rebuilt and any pages currently being viewed will be reloaded in your browser.

Any PRs with fixes or improvements are very welcome!

## Questions

For any questions or comments, please check the [FAQ](https://docs.nautobot.com/projects/pdu-manager/en/latest/user/faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#nautobot`), sign up [here](http://slack.networktocode.com/) if you don't have an account.
