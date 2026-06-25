"""Guard tests that prevent committing sensitive fixture data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
FORBIDDEN_KEY_PARTS = (
    "password",
    "cptoken",
    "refresh_token",
    "refreshtoken",
    "access_token",
    "token_timeout",
)


def _walk_json(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    """Return every JSON key/value path for fixture validation."""
    items: list[tuple[str, Any]] = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            items.extend(_walk_json(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(_walk_json(child, f"{path}[{index}]"))
    return items


def test_fixture_directory_exists() -> None:
    assert FIXTURES.is_dir()


def test_json_fixtures_do_not_contain_tokens_passwords_or_live_identifiers() -> None:
    for fixture in FIXTURES.rglob("*.json"):
        raw_text = fixture.read_text(encoding="utf-8")
        parsed = json.loads(raw_text)

        assert not EMAIL_RE.search(raw_text), f"email-like value found in {fixture}"
        assert not IPV4_RE.search(raw_text), f"IPv4-like value found in {fixture}"

        for path, value in _walk_json(parsed):
            path_lower = path.lower()
            if any(part in path_lower for part in FORBIDDEN_KEY_PARTS):
                assert value in (None, "", "REDACTED", "TOKEN_REDACTED"), (
                    f"sensitive token/password-like field is not redacted: {fixture} {path}"
                )

            if path_lower.endswith(".auth"):
                assert value == "AUTH_REDACTED", (
                    f"Auth must be exactly AUTH_REDACTED in committed fixtures: {fixture} {path}"
                )

            if path_lower.endswith(".gwid"):
                assert isinstance(value, str) and value.startswith("GWID_"), (
                    f"GWID must be synthetic and start with GWID_: {fixture} {path}"
                )

            if path_lower.endswith(".modelid"):
                assert isinstance(value, str) and value.startswith("MODELID_"), (
                    f"ModelID must be synthetic and start with MODELID_: {fixture} {path}"
                )
