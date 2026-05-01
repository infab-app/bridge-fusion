import adsk.core
import bridge_config as config

_command_definitions = []
_handlers = []


def register_commands(ui: adsk.core.UserInterface):
    from bridge_commands.open_bridge import OpenBridgeCommand
    from bridge_commands.view_log import ViewLogCommand

    commands = [
        (
            config.CMD_BRIDGE,
            "Infab Bridge",
            "Open Infab Bridge to browse parts and upload files.",
            config.ICON_BRIDGE,
            OpenBridgeCommand,
        ),
        (
            config.CMD_VIEW_LOG,
            "View Bridge Log",
            "Open the Bridge log file for debugging.",
            "",
            ViewLogCommand,
        ),
    ]

    for cmd_id, name, tooltip, icon, handler_cls in commands:
        cmd_def = ui.commandDefinitions.itemById(cmd_id)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                cmd_id, name, tooltip, icon if icon else ""
            )
        handler = handler_cls()
        cmd_def.commandCreated.add(handler)
        _handlers.append(handler)
        _command_definitions.append(cmd_def)


def unregister_commands(ui: adsk.core.UserInterface):
    for cmd_def in _command_definitions:
        try:
            cmd_def.deleteMe()
        except Exception:
            pass
    _command_definitions.clear()
    _handlers.clear()
