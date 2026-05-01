import threading

import adsk.core
import bridge_config as config

from bridge_lib.settings import Settings

_update_check_event = None
_update_check_handlers = []


def schedule_update_check(app, skip_if_just_updated=False):
    global _update_check_event

    if skip_if_just_updated:
        return

    settings = Settings.reload()
    if not settings.auto_check_updates:
        return

    _update_check_event = app.registerCustomEvent(config.CUSTOM_EVENT_UPDATE_CHECK)
    handler = _UpdateCheckHandler()
    _update_check_event.add(handler)
    _update_check_handlers.append(handler)

    thread = threading.Thread(target=_check_update_after_ready, args=(app, settings.update_channel))
    thread.daemon = True
    thread.start()


def cleanup():
    global _update_check_event
    _update_check_handlers.clear()
    _update_check_event = None


def _check_update_after_ready(app, channel):
    import json
    import time

    deadline = time.monotonic() + config.AUTO_START_READY_TIMEOUT
    while time.monotonic() < deadline:
        try:
            if hasattr(app, "isStartupComplete") and app.isStartupComplete:
                break
            if app.activeViewport is not None:
                break
        except Exception:
            pass
        time.sleep(config.AUTO_START_READY_POLL)

    time.sleep(config.AUTO_START_POST_READY_DELAY)

    try:
        from bridge_lib.updater import check_for_update

        result = check_for_update(channel)
        if result.update_available and not result.error:
            payload = json.dumps(
                {"version": result.latest_version, "prerelease": result.is_prerelease}
            )
            app.fireCustomEvent(config.CUSTOM_EVENT_UPDATE_CHECK, payload)
    except Exception:
        pass


class _UpdateCheckHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            import json

            app = adsk.core.Application.get()
            ui = app.userInterface

            payload = json.loads(args.additionalInfo) if args.additionalInfo else {}
            version = payload.get("version", "")
            prerelease = payload.get("prerelease", False)

            label = f"{version} (beta)" if prerelease else version

            ui.messageBox(
                f"A new version of Bridge is available: {label}\n\n"
                'Use "Check for Updates" in the Bridge toolbar to download it.',
                "Bridge - Update Available",
                adsk.core.MessageBoxButtonTypes.OKButtonType,
                adsk.core.MessageBoxIconTypes.InformationIconType,
            )
        except Exception:
            pass
