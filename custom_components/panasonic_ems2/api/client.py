"""Low-level Panasonic EMS2 HTTP API client."""

from __future__ import annotations

import logging
import time
from http import HTTPStatus
from typing import Any, Literal
from urllib.parse import urlsplit

from .errors import (
    Ems2Expectation,
    Ems2ExceedRateLimit,
    Ems2LoginFailed,
    Ems2TokenNotFound,
    Ems2TooManyRequest,
)

CONTENT_TYPE_JSON = "application/json"

_LOGGER = logging.getLogger(__name__)


def _redact_account(_account: str) -> str:
    """Return a stable placeholder instead of logging Panasonic account IDs."""
    return "<redacted>"


def _safe_endpoint_label(endpoint: Any) -> str:
    """Return a log-safe endpoint label without query parameters or secrets."""
    if not isinstance(endpoint, str):
        return "<invalid-endpoint>"
    try:
        path = urlsplit(endpoint).path
    except ValueError:
        return "<invalid-endpoint>"
    return path or "/"


class PanasonicApiClient:
    """Small HTTP client wrapper for Panasonic EMS2 cloud requests."""

    def __init__(
        self,
        *,
        session,
        account: str,
        user_agent: str = "",
        request_timeout: int = 10,
    ) -> None:
        self._session = session
        self._account = account
        self._user_agent = user_agent
        self._request_timeout = request_timeout
        self.api_counts = 0
        self.api_counts_per_hour = 0

    async def request(
        self,
        method: Literal["GET", "POST"],
        headers: dict[str, Any],
        endpoint: str,
        params=None,
        data=None,
    ):
        """Send one Panasonic EMS2 request and normalize its response shape."""
        res = {}
        headers["user-agent"] = self._user_agent
        headers["Content-Type"] = CONTENT_TYPE_JSON

        self.api_counts = self.api_counts + 1
        self.api_counts_per_hour = self.api_counts_per_hour + 1
        request_start = time.monotonic()
        try:
            response = await self._session.request(
                method,
                url=endpoint,
                json=data,
                params=params,
                headers=headers,
                timeout=self._request_timeout,
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - request_start) * 1000)
            _LOGGER.warning(
                "Failed fetching Panasonic EMS2 data for account=%s method=%s endpoint=%s exception=%s duration_ms=%s",
                _redact_account(self._account),
                method,
                _safe_endpoint_label(endpoint),
                exc.__class__.__name__,
                duration_ms,
            )
            return {}

        if response.status == HTTPStatus.OK:
            try:
                res = await response.json()
            except Exception:
                text = getattr(response, "text", "")
                res = await text() if callable(text) else text
        elif response.status == HTTPStatus.BAD_REQUEST:
            raise Ems2ExceedRateLimit
        elif response.status == HTTPStatus.FORBIDDEN:
            raise Ems2LoginFailed
        elif response.status == HTTPStatus.TOO_MANY_REQUESTS:
            raise Ems2TooManyRequest
        elif response.status == HTTPStatus.EXPECTATION_FAILED:
            raise Ems2Expectation
        elif response.status == HTTPStatus.NOT_FOUND:
            _LOGGER.warning("Use wrong method or parameters")
            res = {}
        elif response.status == HTTPStatus.METHOD_NOT_ALLOWED:
            _LOGGER.warning("The method is not allowed")
            res = {}
        elif response.status == 429:
            _LOGGER.warning("Wrong")
            res = {}
        else:
            _LOGGER.error("request %s", response)
            raise Ems2TokenNotFound

        if isinstance(res, str):
            return {"data": res}

        if isinstance(res, list):
            return {"data": res}

        if isinstance(res, dict):
            return res

        return res
