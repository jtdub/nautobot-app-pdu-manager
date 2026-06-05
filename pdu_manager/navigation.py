"""Menu items."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items = (
    NavMenuItem(
        link="plugins:pdu_manager:pdumanager_list",
        name="Pdu Manager",
        permissions=["pdu_manager.view_pdumanager"],
        buttons=(
            NavMenuAddButton(
                link="plugins:pdu_manager:pdumanager_add",
                permissions=["pdu_manager.add_pdumanager"],
            ),
        ),
    ),
)

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="Pdu Manager", items=tuple(items)),),
    ),
)
