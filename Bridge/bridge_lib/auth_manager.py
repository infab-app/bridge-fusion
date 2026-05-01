import json
import logging
import threading
import urllib.error
from typing import Optional

import bridge_config as config

from bridge_lib.infab_client import InfabClient
from bridge_lib.integrity import is_envelope, unwrap_and_verify, wrap_with_checksum
from bridge_lib.path_validation import secure_file_permissions, secure_mkdir
from bridge_lib.settings import Settings

logger = logging.getLogger("bridge")


class AuthManager:
    _instance: Optional["AuthManager"] = None

    def __init__(self):
        self._session_key: Optional[str] = None
        self._user_info: Optional[dict] = None
        self._client: Optional[InfabClient] = None
        self._refresh_timer: Optional[threading.Timer] = None

    @classmethod
    def instance(cls) -> "AuthManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_signed_in(self) -> bool:
        return self._session_key is not None

    @property
    def session_key(self) -> Optional[str]:
        return self._session_key

    @property
    def user_info(self) -> Optional[dict]:
        return self._user_info

    @property
    def client(self) -> Optional[InfabClient]:
        return self._client

    def _get_client(self) -> InfabClient:
        if self._client is None:
            settings = Settings.instance()
            self._client = InfabClient(settings.api_url, self._session_key)
        self._client.session_key = self._session_key
        return self._client

    def exchange_and_set_session(self, exchange_token: str) -> bool:
        """Exchanges a one-time token for a session key and establishes the session."""
        settings = Settings.instance()
        client = InfabClient(settings.api_url)
        try:
            session_key = client.exchange_token(exchange_token)
            return self.set_session(session_key)
        except Exception:
            logger.error("Token exchange failed")
            return False

    def set_session(self, session_key: str) -> bool:
        self._session_key = session_key
        client = self._get_client()
        try:
            self._user_info = client.authenticate()
            self._save_session()
            self._start_refresh_timer()
            logger.info("Bridge session established")
            return True
        except Exception:
            logger.error("Failed to validate session")
            self._session_key = None
            self._user_info = None
            return False

    def update_session_key(self, new_key: str):
        """Updates the session key after server-side rotation without re-validating."""
        self._session_key = new_key
        if self._client:
            self._client.session_key = new_key
        self._save_session()

    def sign_out(self):
        if self._session_key:
            try:
                client = self._get_client()
                client.sign_out()
            except Exception:
                logger.warning("Failed to call signout endpoint")
        self._session_key = None
        self._user_info = None
        self._stop_refresh_timer()
        self._delete_session_file()
        logger.info("Signed out of Bridge")

    def load_session(self):
        session_file = config.SESSION_FILE
        if not session_file.exists():
            return
        try:
            with open(session_file, encoding="utf-8") as f:
                raw = json.load(f)
            if is_envelope(raw):
                data = unwrap_and_verify(raw)
                if data is None:
                    logger.warning("Session file integrity check failed")
                    self._delete_session_file()
                    return
            else:
                self._delete_session_file()
                return
            key = data.get("session_key")
            if not key:
                self._delete_session_file()
                return
            self._session_key = key
            client = self._get_client()
            self._user_info = client.authenticate()
            self._start_refresh_timer()
            logger.info("Restored Bridge session from disk")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                logger.warning("Session rejected by server, clearing")
                self._session_key = None
                self._user_info = None
                self._delete_session_file()
            else:
                # Keep session key in memory for IPC injection; server may be temporarily down
                logger.warning(
                    f"Server returned {e.code} during session restore, keeping session on disk"
                )
                self._user_info = None
        except Exception:
            # Network error — keep session file for next attempt
            logger.warning("Network error during session restore, keeping session on disk")
            self._user_info = None

    def _save_session(self):
        secure_mkdir(config.SESSION_FILE.parent)
        data = {"session_key": self._session_key}
        envelope = wrap_with_checksum(data)
        tmp = config.SESSION_FILE.with_suffix(f".tmp.{__import__('uuid').uuid4().hex[:8]}")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(envelope, f)
        tmp.replace(config.SESSION_FILE)
        secure_file_permissions(config.SESSION_FILE)

    def _delete_session_file(self):
        try:
            config.SESSION_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    def _start_refresh_timer(self):
        self._stop_refresh_timer()
        self._refresh_timer = threading.Timer(
            config.SESSION_REFRESH_INTERVAL, self._refresh_session
        )
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

    def _stop_refresh_timer(self):
        if self._refresh_timer:
            self._refresh_timer.cancel()
            self._refresh_timer = None

    def _refresh_session(self):
        if not self._session_key:
            return
        try:
            client = self._get_client()
            self._user_info = client.authenticate()
            logger.info("Session refreshed")
            self._start_refresh_timer()
        except Exception:
            logger.warning("Session refresh failed")
            self._session_key = None
            self._user_info = None
            self._delete_session_file()
