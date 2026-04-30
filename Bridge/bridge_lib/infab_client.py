import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

import bridge_config as config

logger = logging.getLogger("bridge")


class InfabClient:
    def __init__(self, api_url: str, session_key: Optional[str] = None):
        self._api_url = api_url.rstrip("/")
        self._session_key = session_key

    @property
    def session_key(self) -> Optional[str]:
        return self._session_key

    @session_key.setter
    def session_key(self, value: Optional[str]):
        self._session_key = value

    def _request(
        self,
        method: str,
        url: str,
        body: Optional[bytes] = None,
        headers: Optional[dict] = None,
        timeout: int = config.HTTP_TIMEOUT,
    ) -> tuple[int, bytes]:
        hdrs = headers or {}
        if self._session_key:
            hdrs["Cookie"] = f"infab_bridgeAuth={self._session_key}"
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except urllib.error.URLError as e:
            logger.error(f"Request failed: {e.reason}")
            raise

    def _trpc_url(self, procedure: str) -> str:
        return f"{self._api_url}/bridge/trpc/{procedure}"

    def trpc_query(self, procedure: str, input_data: Any = None) -> dict:
        url = self._trpc_url(procedure)
        if input_data is not None:
            encoded = urllib.request.quote(json.dumps(input_data))
            url = f"{url}?input={encoded}"
        status, body = self._request("GET", url, headers={"Content-Type": "application/json"})
        result = json.loads(body)
        if status >= 400:
            error_msg = result.get("error", {}).get("message", "Unknown error")
            raise Exception(f"tRPC query failed ({status}): {error_msg}")
        return result.get("result", {}).get("data", result)

    def trpc_mutation(self, procedure: str, input_data: Any = None) -> dict:
        url = self._trpc_url(procedure)
        body = json.dumps(input_data).encode("utf-8") if input_data is not None else None
        status, resp_body = self._request(
            "POST", url, body=body, headers={"Content-Type": "application/json"}
        )
        result = json.loads(resp_body)
        if status >= 400:
            error_msg = result.get("error", {}).get("message", "Unknown error")
            raise Exception(f"tRPC mutation failed ({status}): {error_msg}")
        return result.get("result", {}).get("data", result)

    def exchange_token(self, token: str) -> str:
        """Exchanges a one-time token for a session key. Does not require an existing session."""
        result = self.trpc_mutation("auth.exchange", {"token": token})
        session_key = result.get("sessionKey")
        if not session_key:
            raise Exception("Exchange returned no session key")
        return session_key

    def authenticate(self) -> dict:
        return self.trpc_query("auth.authenticate")

    def sign_out(self) -> dict:
        return self.trpc_mutation("auth.signout")

    def upload_to_s3(self, presigned_url: str, file_path: str, content_type: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found for S3 upload: {file_path}")
            return False
        data = path.read_bytes()
        try:
            status, _ = self._request(
                "PUT",
                presigned_url,
                body=data,
                headers={"Content-Type": content_type},
                timeout=config.S3_UPLOAD_TIMEOUT,
            )
            if status < 300:
                logger.info(f"Uploaded to S3: {path.name} ({len(data)} bytes)")
                return True
            logger.error(f"S3 upload failed with status {status}: {path.name}")
            return False
        except Exception:
            logger.error(f"S3 upload error: {path.name}")
            return False
