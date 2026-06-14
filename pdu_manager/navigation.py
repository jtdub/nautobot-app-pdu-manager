"""Menu items for pdu_manager."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items = (
    NavMenuItem(
        link="plugins:pdu_manager:poweroffprotection_list",
        name="Power Off Protections",
        permissions=["pdu_manager.view_poweroffprotection"],
        buttons=(
            NavMenuAddButton(
                link="plugins:pdu_manager:poweroffprotection_add",
                permissions=["pdu_manager.add_poweroffprotection"],
            ),
        ),
    ),
    NavMenuItem(
        link="plugins:pdu_manager:pducommandset_list",
        name="PDU Command Sets",
        permissions=["pdu_manager.view_pducommandset"],
        buttons=(
            NavMenuAddButton(
                link="plugins:pdu_manager:pducommandset_add",
                permissions=["pdu_manager.add_pducommandset"],
            ),
        ),
    ),
)

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="PDU Manager", items=tuple(items)),),
    ),
)
