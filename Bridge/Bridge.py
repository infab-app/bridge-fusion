import os
import sys
import traceback

import adsk.core
import adsk.fusion

_addin_path = os.path.dirname(os.path.abspath(__file__))
if _addin_path not in sys.path:
    sys.path.insert(0, _addin_path)

import bridge_config as config
from bridge_lib import ui_components
from bridge_lib.auth_manager import AuthManager
from bridge_lib.bridge_logger import BridgeLogger
from bridge_lib.palette_manager import PaletteManager

_app = None
_ui = None


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        BridgeLogger.instance().start()
        BridgeLogger.instance().info("STARTUP", "Bridge add-in started")

        AuthManager.instance().load_session()

        ui_components.create_ui(_app)

    except Exception:
        if _ui:
            _ui.messageBox(f"Bridge failed to start:\n{traceback.format_exc()}")


def stop(context):
    try:
        PaletteManager.instance().destroy_all()

        if _app:
            ui_components.destroy_ui(_app)

    except Exception:
        if _ui:
            _ui.messageBox(f"Bridge error during shutdown:\n{traceback.format_exc()}")
