"""Home Assistant token storage adapter for Panasonic EMS2."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.storage import Store

from ..core.const import (
    CONF_CPTOKEN,
    CONF_REFRESH_TOKEN,
    CONF_REFRESH_TOKEN_TIMEOUT,
    CONF_TOKEN_TIMEOUT,
    DOMAIN,
)

DEFAULT_TOKENS = {
    CONF_CPTOKEN: "",
    CONF_TOKEN_TIMEOUT: "20200101010100",
    CONF_REFRESH_TOKEN: "",
    CONF_REFRESH_TOKEN_TIMEOUT: "20200101010100",
}


class PanasonicTokenStore:
    """HA Store wrapper for per-account Panasonic EMS2 tokens."""

    def __init__(self, hass, account: str) -> None:
        self._hass = hass
        self._account = account
        self._store = Store(hass, 1, f"{DOMAIN}/tokens.json")

    async def load_tokens(self) -> dict:
        """Load tokens for this account, falling back to expired defaults."""
        data = await self._store.async_load() or None
        if not data:
            return dict(DEFAULT_TOKENS)
        return data.get(self._account, dict(DEFAULT_TOKENS))

    async def store_tokens(self, tokens: dict) -> None:
        """Store tokens for this account while preserving other accounts."""
        data = await self._store.async_load() or {}
        data[self._account] = tokens
        await self._store.async_save(data)

    async def active_account_count(self, now: datetime | None = None) -> int:
        """Return number of accounts with a non-expired access token."""
        data = await self._store.async_load() or None
        if not data:
            return 1

        if now is None:
            now = datetime.now()

        def parse_token_timeout(token_timeout) -> datetime | None:
            if (
                not isinstance(token_timeout, str)
                or len(token_timeout) != 14
                or not token_timeout.isdigit()
            ):
                return None

            try:
                return datetime(
                    int(token_timeout[:4]),
                    int(token_timeout[4:6]),
                    int(token_timeout[6:8]),
                    int(token_timeout[8:10]),
                    int(token_timeout[10:12]),
                    int(token_timeout[12:])
                )
            except ValueError:
                return None

        accounts = 0
        for _, value in data.items():
            if not isinstance(value, dict):
                continue

            timeout = parse_token_timeout(value.get(CONF_TOKEN_TIMEOUT))
            if timeout is None:
                continue

            if int(timeout.timestamp() - now.timestamp()) > 0:
                accounts = accounts + 1

        return max(accounts, 1)

    def async_listen_save_on_stop(self, tokens_provider: Callable[[], dict]) -> None:
        """Save latest tokens once when Home Assistant stops."""

        async def stop(*args):
            await self.store_tokens(tokens_provider())

        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop)
