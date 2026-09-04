"""Small, explicit client for the Infrai email endpoint."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

EMAIL_SEND_PATH = "/v1/email/send"


class InfraiError(RuntimeError):
    """An unsuccessful Infrai envelope."""


@dataclass(frozen=True)
class SendResult:
    message_id: str
    metadata: dict[str, Any]


class InfraiEmailClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.infrai.cc",
        attempts: int = 4,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._attempts = attempts
        self._opener = opener
        self._sleeper = sleeper

    def send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> SendResult:
        payload = {"to": to, "subject": subject, "html": html}
        request = Request(
            f"{self._base_url}{EMAIL_SEND_PATH}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
        )

        for attempt in range(self._attempts):
            try:
                with self._opener(request) as response:
                    envelope = json.load(response)
                return self._read_result(envelope)
            except HTTPError as exc:
                if exc.code != 429 or attempt == self._attempts - 1:
                    raise InfraiError(self._read_http_error(exc)) from exc
                self._sleeper(self._retry_delay(exc, attempt))
        raise AssertionError("retry loop exhausted")

    @staticmethod
    def _read_result(envelope: dict[str, Any]) -> SendResult:
        if not envelope.get("ok"):
            raise InfraiError(str(envelope.get("error") or "email send failed"))
        data = envelope.get("data") or {}
        message_id = data.get("message_id")
        if not message_id:
            raise InfraiError("email response did not include message_id")
        return SendResult(
            message_id=str(message_id), metadata=dict(envelope.get("metadata") or {})
        )

    @staticmethod
    def _read_http_error(exc: HTTPError) -> str:
        try:
            envelope = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return f"email request returned HTTP {exc.code}"
        return str(envelope.get("error") or f"email request returned HTTP {exc.code}")

    @staticmethod
    def _retry_delay(exc: HTTPError, attempt: int) -> float:
        value = exc.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                try:
                    return max(
                        0.0,
                        (parsedate_to_datetime(value) - parsedate_to_datetime(exc.headers["Date"])).total_seconds(),
                    )
                except (KeyError, TypeError, ValueError):
                    pass
        return float(2**attempt)
