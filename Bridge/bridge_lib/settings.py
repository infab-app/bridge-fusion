import json
import logging
from pathlib import Path
from typing import Optional

import bridge_config as config

from bridge_lib.integrity import is_envelope, unwrap_and_verify, wrap_with_checksum
from bridge_lib.path_validation import secure_file_permissions, secure_mkdir

logger = logging.getLogger("bridge")

_DEFAULTS = {
    "auth_url": config.AUTH_URL,
    "bridge_app_url": config.BRIDGE_APP_URL,
    "api_url": config.API_URL,
    "version": 1,
}


class Settings:
    _instance: Optional["Settings"] = None

    def __init__(self):
        self._data: dict = dict(_DEFAULTS)
        self._load()

    @classmethod
    def instance(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reload(cls) -> "Settings":
        cls._instance = cls()
        return cls._instance

    def _load(self):
        settings_file = Path(config.SETTINGS_FILE)
        if not settings_file.exists():
            return
        try:
            with open(settings_file, encoding="utf-8") as f:
                raw = json.load(f)
            if is_envelope(raw):
                stored = unwrap_and_verify(raw)
                if stored is None:
                    return
            else:
                return
            for key in _DEFAULTS:
                if key in stored:
                    self._data[key] = stored[key]
        except (json.JSONDecodeError, OSError):
            pass

    def save(self):
        settings_file = Path(config.SETTINGS_FILE)
        secure_mkdir(settings_file.parent)
        envelope = wrap_with_checksum(self._data)
        tmp_file = settings_file.with_suffix(f".tmp.{__import__('uuid').uuid4().hex[:8]}")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
        tmp_file.replace(settings_file)
        secure_file_permissions(settings_file)

    @property
    def auth_url(self) -> str:
        return self._data.get("auth_url", config.AUTH_URL)

    @auth_url.setter
    def auth_url(self, value: str):
        self._data["auth_url"] = value

    @property
    def bridge_app_url(self) -> str:
        return self._data.get("bridge_app_url", config.BRIDGE_APP_URL)

    @bridge_app_url.setter
    def bridge_app_url(self, value: str):
        self._data["bridge_app_url"] = value

    @property
    def api_url(self) -> str:
        return self._data.get("api_url", config.API_URL)

    @api_url.setter
    def api_url(self, value: str):
        self._data["api_url"] = value
