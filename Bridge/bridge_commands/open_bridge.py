import traceback

import adsk.core

from bridge_lib.palette_manager import PaletteManager

_handlers = []


class OpenBridgeCommand(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            execute_handler = _OpenBridgeExecuteHandler()
            cmd.execute.add(execute_handler)
            _handlers.append(execute_handler)
            cmd.isAutoExecute = True
        except Exception:
            app = adsk.core.Application.get()
            app.userInterface.messageBox(
                f"Open Bridge failed:\n{traceback.format_exc()}"
            )


class _OpenBridgeExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            PaletteManager.instance().show_bridge_palette()
        except Exception:
            app = adsk.core.Application.get()
            app.userInterface.messageBox(
                f"Open Bridge failed:\n{traceback.format_exc()}"
            )
