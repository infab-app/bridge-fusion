import os
import sys
import traceback

import adsk.core
import adsk.fusion

_addin_path = os.path.dirname(os.path.abspath(__file__))
if _addin_path not in sys.path:
    sys.path.insert(0, _addin_path)


def _copy_dir_contents(src, dest, *, overwrite=False, skip_dotfiles=False):
    import shutil

    for item in src.iterdir():
        if skip_dotfiles and item.name.startswith("."):
            continue
        if item.is_symlink():
            continue
        target = dest / item.name
        if item.is_dir():
            if overwrite and target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target, symlinks=False)
        else:
            shutil.copy2(item, target)


def _apply_pending_update():
    import json
    import shutil
    from pathlib import Path

    if sys.platform == "win32":
        base_dir = Path(os.environ.get("APPDATA", Path.home())) / ".bridge"
    else:
        base_dir = Path.home() / ".bridge"

    pending_file = base_dir / "update_pending.json"
    if not pending_file.exists():
        return False

    try:
        with open(pending_file, encoding="utf-8") as f:
            pending = json.load(f)

        from bridge_lib.integrity import is_envelope, unwrap_and_verify

        if is_envelope(pending):
            payload = unwrap_and_verify(pending)
            if payload is None:
                pending_file.unlink(missing_ok=True)
                return False
            pending = payload
        else:
            pending_file.unlink(missing_ok=True)
            return False

        staging_path = Path(pending["staging_path"])
        staging_base = base_dir / "update_staging"
        resolved_staging = staging_path.resolve()
        if not resolved_staging.is_relative_to(staging_base.resolve()):
            pending_file.unlink(missing_ok=True)
            return False
        if staging_path.is_symlink():
            pending_file.unlink(missing_ok=True)
            return False
        if not staging_path.exists():
            pending_file.unlink(missing_ok=True)
            return False

        addin_dir = Path(_addin_path)
        backup_dir = base_dir / "update_backup"

        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        _copy_dir_contents(addin_dir, backup_dir, skip_dotfiles=True)

        try:
            _copy_dir_contents(staging_path, addin_dir, overwrite=True)
        except Exception:
            _copy_dir_contents(backup_dir, addin_dir, overwrite=True)
            pending_file.unlink(missing_ok=True)
            return False

        shutil.rmtree(backup_dir, ignore_errors=True)
        staging_parent = staging_path.parent
        if staging_parent.name == "extracted":
            shutil.rmtree(staging_parent.parent, ignore_errors=True)
        else:
            shutil.rmtree(staging_parent, ignore_errors=True)
        pending_file.unlink(missing_ok=True)
        return True

    except Exception:
        try:
            pending_file.unlink(missing_ok=True)
        except Exception:
            pass
        return False


_update_applied = _apply_pending_update()

import bridge_config as config  # noqa: E402
from bridge_lib import ui_components  # noqa: E402
from bridge_lib.auth_manager import AuthManager  # noqa: E402
from bridge_lib.bridge_logger import BridgeLogger  # noqa: E402
from bridge_lib.palette_manager import PaletteManager  # noqa: E402
from bridge_lib.update_check import cleanup as cleanup_update_check  # noqa: E402
from bridge_lib.update_check import schedule_update_check  # noqa: E402

_app = None
_ui = None


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        BridgeLogger.instance().start()
        BridgeLogger.instance().info("STARTUP", "Bridge add-in started")

        if _update_applied:
            _ui.messageBox(
                f"Bridge has been updated to version {config.VERSION}.\n\n"
                "See the release notes on GitHub for details.",
                "Bridge - Updated",
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.InformationIconType,
            )

        AuthManager.instance().load_session()

        ui_components.create_ui(_app)

        schedule_update_check(_app, skip_if_just_updated=_update_applied)

    except Exception:
        if _ui:
            _ui.messageBox(f"Bridge failed to start:\n{traceback.format_exc()}")


def stop(context):
    try:
        PaletteManager.instance().destroy_all()

        try:
            if _app:
                _app.unregisterCustomEvent(config.CUSTOM_EVENT_UPDATE_CHECK)
        except Exception:
            pass

        cleanup_update_check()

        if _app:
            ui_components.destroy_ui(_app)

    except Exception:
        if _ui:
            _ui.messageBox(f"Bridge error during shutdown:\n{traceback.format_exc()}")
