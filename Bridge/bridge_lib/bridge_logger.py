import datetime
import json
import platform
import threading
from pathlib import Path

import adsk.core

import bridge_config as config
from bridge_lib.path_validation import secure_file_permissions, secure_mkdir


class BridgeLogger:
    _instance = None

    def __init__(self):
        self._log_dir = config.LOG_DIR
        self._lock = threading.Lock()
        self._current_log_file = None
        self._dropped_entries = 0

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self):
        secure_mkdir(self._log_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_log_file = self._log_dir / f"bridge_{timestamp}.jsonl"

    def log(self, event: str, detail: str, severity: str = "INFO"):
        with self._lock:
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "event": event,
                "detail": detail,
                "severity": severity,
                "user": self._get_user(),
                "machine": platform.node(),
            }

            log_file = self._current_log_file
            if log_file is None:
                secure_mkdir(self._log_dir)
                log_file = self._log_dir / "bridge_unsessioned.jsonl"

            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
                secure_file_permissions(log_file)
            except OSError:
                self._dropped_entries += 1

    def info(self, event: str, detail: str):
        self.log(event, detail, "INFO")

    def error(self, event: str, detail: str):
        self.log(event, detail, "ERROR")

    def warning(self, event: str, detail: str):
        self.log(event, detail, "WARNING")

    def get_current_log_path(self):
        return self._current_log_file

    def get_log_dir(self):
        return self._log_dir

    @staticmethod
    def _get_user():
        try:
            app = adsk.core.Application.get()
            return app.userName or "unknown"
        except Exception:
            return "unknown"
