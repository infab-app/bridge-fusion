import json
import os
import shutil
import traceback
import urllib.request
import uuid
from typing import Optional

import adsk.core
import adsk.fusion
import bridge_config as config

from bridge_lib.auth_manager import AuthManager
from bridge_lib.bridge_logger import BridgeLogger
from bridge_lib.export_manager import ExportManager
from bridge_lib.path_validation import secure_mkdir, validate_filename, validate_url


class _PaletteHTMLHandler(adsk.core.HTMLEventHandler):
    """Routes incoming HTML events from Palettes to the PaletteManager."""

    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.HTMLEventArgs):
        try:
            PaletteManager.instance().handle_html_event(args)
        except Exception:
            BridgeLogger.instance().error("PALETTE_EVENT_ERROR", traceback.format_exc())


class _PaletteCloseHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        pass


class PaletteManager:
    _instance: Optional["PaletteManager"] = None

    def __init__(self):
        self._palettes: dict[str, adsk.core.Palette] = {}
        self._handlers: list = []
        self._export_paths: dict[str, dict[str, str]] = {}

    @classmethod
    def instance(cls) -> "PaletteManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def show_bridge_palette(self):
        """Opens the bridge app Palette pointed at bridge.infab.app."""
        from bridge_lib.settings import Settings

        app = adsk.core.Application.get()
        ui = app.userInterface

        palette = ui.palettes.itemById(config.PALETTE_BRIDGE_ID)
        if palette:
            palette.isVisible = True
            return

        bridge_url = Settings.instance().bridge_app_url
        html_handler = _PaletteHTMLHandler()
        self._handlers.append(html_handler)

        palette = ui.palettes.add(
            config.PALETTE_BRIDGE_ID,
            config.PALETTE_BRIDGE_NAME,
            bridge_url,
            True,
            True,
            True,
            config.PALETTE_BRIDGE_WIDTH,
            config.PALETTE_BRIDGE_HEIGHT,
            True,
        )

        palette.incomingFromHTML.add(html_handler)
        self._palettes[config.PALETTE_BRIDGE_ID] = palette
        palette.isVisible = True

    def close_palette(self, palette_id: str):
        app = adsk.core.Application.get()
        palette = app.userInterface.palettes.itemById(palette_id)
        if palette:
            palette.isVisible = False

    def send_to_palette(self, palette_id: str, action: str, data: dict):
        app = adsk.core.Application.get()
        palette = app.userInterface.palettes.itemById(palette_id)
        if palette and palette.isVisible:
            palette.sendInfoToHTML(action, json.dumps(data))

    def destroy_all(self):
        app = adsk.core.Application.get()
        if not app:
            return
        ui = app.userInterface
        for pid in list(self._palettes.keys()):
            try:
                palette = ui.palettes.itemById(pid)
                if palette:
                    palette.deleteMe()
            except Exception:
                pass
        self._palettes.clear()
        self._handlers.clear()

    def handle_html_event(self, args: adsk.core.HTMLEventArgs):
        """Routes events from Palette HTML to appropriate handlers."""
        action = args.action
        BridgeLogger.instance().info("PALETTE_EVENT", f"action={action}")
        try:
            data = json.loads(args.data) if args.data else {}
        except (json.JSONDecodeError, TypeError):
            data = {}

        if action == "auth-complete":
            token = data if isinstance(data, str) else data.get("sessionKey", "")
            self._handle_auth_complete(token)
        elif action == "request-session":
            self._handle_request_session()
        elif action == "session-rotated":
            self._handle_session_rotated(data)
        elif action == "export":
            self._handle_export(data)
        elif action == "upload":
            self._handle_upload(data)
        elif action == "open-file":
            self._handle_open_file(data)
        elif action == "sign-out":
            self._handle_sign_out()

    def _handle_auth_complete(self, exchange_token):
        """Receives exchange token from auth page and exchanges it for a session."""
        if isinstance(exchange_token, str) and exchange_token:
            if AuthManager.instance().exchange_and_set_session(exchange_token):
                BridgeLogger.instance().info(
                    "AUTH_COMPLETE", "Session established via token exchange"
                )
            else:
                BridgeLogger.instance().warning("AUTH_EXCHANGE_FAILED", "Token exchange failed")
        else:
            BridgeLogger.instance().warning(
                "AUTH_EMPTY_TOKEN",
                "Received empty exchange token from auth",
            )

    def _handle_request_session(self):
        """Responds to the bridge web app's request for a stored session key."""
        auth = AuthManager.instance()
        self.send_to_palette(
            config.PALETTE_BRIDGE_ID,
            "set-session",
            {
                "sessionKey": auth.session_key,
            },
        )

    def _handle_session_rotated(self, data: dict):
        """Updates the stored session key after server-side rotation."""
        new_key = data.get("sessionKey", "")
        if new_key:
            AuthManager.instance().update_session_key(new_key)
            BridgeLogger.instance().info("SESSION_ROTATED", "Session key rotated")

    def _handle_export(self, data: dict):
        """Exports design files to temp directory and sends paths back to Palette."""
        formats = data.get("formats", [])
        export_id = uuid.uuid4().hex[:12]
        export_dir = config.TEMP_EXPORT_DIR / export_id
        secure_mkdir(export_dir)

        app = adsk.core.Application.get()
        doc = app.activeDocument
        if not doc:
            self.send_to_palette(
                config.PALETTE_BRIDGE_ID, "export-error", {"error": "No active document"}
            )
            return

        design_name = doc.name.replace(" ", "_")
        results = []

        format_exporters = {
            "f3d": (ExportManager.export_fusion_archive, f"{design_name}.f3d"),
            "step": (ExportManager.export_step, f"{design_name}.step"),
            "stl": (ExportManager.export_stl, f"{design_name}.stl"),
            "igs": (ExportManager.export_iges, f"{design_name}.igs"),
        }

        for fmt in formats:
            if fmt not in format_exporters:
                continue
            exporter, filename = format_exporters[fmt]
            filepath = str(export_dir / filename)
            success = exporter(filepath)
            if success:
                file_size = os.path.getsize(filepath)
                results.append(
                    {
                        "format": fmt,
                        "filename": filename,
                        "filepath": filepath,
                        "size": file_size,
                    }
                )

        self._export_paths[export_id] = {r["filename"]: r["filepath"] for r in results}

        self.send_to_palette(
            config.PALETTE_BRIDGE_ID,
            "export-complete",
            {
                "exportId": export_id,
                "files": [
                    {"format": r["format"], "filename": r["filename"], "size": r["size"]}
                    for r in results
                ],
            },
        )

    def _handle_upload(self, data: dict):
        """Uploads exported files to S3 using presigned URLs."""
        export_id = data.get("exportId", "")
        files = data.get("files", [])
        paths = self._export_paths.get(export_id, {})
        auth = AuthManager.instance()
        client = auth.client
        if not client:
            self.send_to_palette(
                config.PALETTE_BRIDGE_ID, "upload-error", {"error": "Not signed in"}
            )
            return

        results = []
        for file_info in files:
            filename = file_info.get("filename", "")
            filepath = paths.get(filename)
            presigned_url = file_info.get("presignedUrl", "")
            content_type = file_info.get("contentType", "application/octet-stream")
            resource_uuid = file_info.get("uuid")

            if not filepath or not presigned_url:
                continue
            if not validate_url(presigned_url):
                BridgeLogger.instance().warning(
                    "UPLOAD_REJECTED",
                    f"URL rejected (non-HTTPS): {presigned_url[:80]}",
                )
                continue

            success = client.upload_to_s3(presigned_url, filepath, content_type)
            results.append(
                {
                    "uuid": resource_uuid,
                    "success": success,
                    "filename": filename,
                }
            )

        self.send_to_palette(
            config.PALETTE_BRIDGE_ID,
            "upload-complete",
            {
                "results": results,
            },
        )

        if export_id and export_id in self._export_paths:
            export_dir = config.TEMP_EXPORT_DIR / export_id
            if export_dir.exists():
                shutil.rmtree(export_dir, ignore_errors=True)
            del self._export_paths[export_id]

    def _handle_open_file(self, data: dict):
        """Downloads a file from a presigned URL and opens it in Fusion 360."""
        app = adsk.core.Application.get()
        ui = app.userInterface

        url = data.get("url", "")
        filename = data.get("filename", "")
        log = BridgeLogger.instance()
        log.info("OPEN_FILE", f"filename={filename}, url_length={len(url)}")

        if not url or not filename or not validate_filename(filename):
            msg = f"Invalid file URL or filename (url={bool(url)}, filename={repr(filename)})"
            log.error("OPEN_FILE_INVALID", msg)
            ui.messageBox(msg, "Bridge: Open File Error")
            self.send_to_palette(config.PALETTE_BRIDGE_ID, "open-file-error", {"error": msg})
            return

        if not validate_url(url):
            msg = "URL rejected: non-HTTPS scheme"
            log.error("OPEN_FILE_URL_REJECTED", msg)
            ui.messageBox(msg, "Bridge: Open File Error")
            self.send_to_palette(config.PALETTE_BRIDGE_ID, "open-file-error", {"error": msg})
            return

        download_dir = config.TEMP_EXPORT_DIR / f"download_{uuid.uuid4().hex[:12]}"
        secure_mkdir(download_dir)
        filepath = str(download_dir / filename)

        try:
            log.info("OPEN_FILE_DOWNLOAD", f"downloading to {filepath}")
            urllib.request.urlretrieve(url, filepath)
            log.info("OPEN_FILE_DOWNLOADED", f"{filename} ({os.path.getsize(filepath)} bytes)")
        except Exception:
            msg = f"Download failed: {traceback.format_exc()}"
            log.error("OPEN_FILE_DOWNLOAD_FAILED", msg)
            ui.messageBox(msg, "Bridge: Download Error")
            shutil.rmtree(download_dir, ignore_errors=True)
            self.send_to_palette(
                config.PALETTE_BRIDGE_ID, "open-file-error", {"error": "Failed to download file"}
            )
            return

        try:
            ext = os.path.splitext(filename)[1].lower()
            log.info("OPEN_FILE_IMPORT", f"importing {filename} (ext={ext})")

            if ext == ".f3d":
                app.open(filepath)
            else:
                import_mgr = app.importManager
                if ext in (".step", ".stp"):
                    options = import_mgr.createSTEPImportOptions(filepath)
                elif ext in (".igs", ".iges"):
                    options = import_mgr.createIGESImportOptions(filepath)
                elif ext == ".stl":
                    options = import_mgr.createSTLImportOptions(filepath)
                elif ext == ".sat":
                    options = import_mgr.createSATImportOptions(filepath)
                elif ext == ".smt":
                    options = import_mgr.createSMTImportOptions(filepath)
                else:
                    options = import_mgr.createSTEPImportOptions(filepath)
                import_mgr.importToNewDocument(options)

            log.info("OPEN_FILE_SUCCESS", f"opened {filename} in Fusion")
            self.send_to_palette(
                config.PALETTE_BRIDGE_ID,
                "open-file-complete",
                {
                    "filename": filename,
                },
            )
        except Exception:
            msg = f"Import failed: {traceback.format_exc()}"
            log.error("OPEN_FILE_IMPORT_FAILED", msg)
            ui.messageBox(msg, "Bridge: Import Error")
            self.send_to_palette(
                config.PALETTE_BRIDGE_ID,
                "open-file-error",
                {"error": "Failed to open file in Fusion"},
            )

    def _handle_sign_out(self):
        auth = AuthManager.instance()
        auth.sign_out()

        app = adsk.core.Application.get()
        palette = app.userInterface.palettes.itemById(config.PALETTE_BRIDGE_ID)
        if palette:
            palette.deleteMe()
            self._palettes.pop(config.PALETTE_BRIDGE_ID, None)

        self.show_bridge_palette()
