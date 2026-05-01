import subprocess
import sys
import traceback

import adsk.core
from bridge_lib.bridge_logger import BridgeLogger

_handlers = []


class ViewLogCommand(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isAutoExecute = True
            execute_handler = _ViewLogExecuteHandler()
            cmd.execute.add(execute_handler)
            _handlers.append(execute_handler)
        except Exception:
            app = adsk.core.Application.get()
            app.userInterface.messageBox(f"View Log failed:\n{traceback.format_exc()}")


class _ViewLogExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            logger = BridgeLogger.instance()
            log_path = logger.get_current_log_path()

            if log_path is None or not log_path.exists():
                log_path = logger.get_log_dir()
                if not log_path.exists():
                    app = adsk.core.Application.get()
                    app.userInterface.messageBox(
                        "No logs found.\n\nLogs will be created when Bridge actions are performed.",
                        "Bridge - Logs",
                    )
                    return

            path_str = str(log_path)
            if sys.platform == "win32":
                import os

                if log_path.is_file():
                    subprocess.Popen(["explorer", "/select,", path_str])
                else:
                    os.startfile(path_str)
            else:
                if log_path.is_file():
                    subprocess.Popen(["open", "-R", path_str])
                else:
                    subprocess.Popen(["open", path_str])
        except Exception:
            app = adsk.core.Application.get()
            app.userInterface.messageBox(f"Failed to open log:\n{traceback.format_exc()}")
