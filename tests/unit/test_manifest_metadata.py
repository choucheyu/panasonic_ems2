"""Metadata tests for the Panasonic Smart IoT TW custom integration."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = ROOT / "custom_components" / "panasonic_ems2"
REPO_URL = "https://github.com/choucheyu/panasonic_ems2"
ISSUES_URL = f"{REPO_URL}/issues"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def test_manifest_identity_matches_taiwan_fork() -> None:
    manifest = _load_json(INTEGRATION / "manifest.json")

    assert manifest["domain"] == "panasonic_ems2"
    assert manifest["name"] == "Panasonic Smart IoT TW"
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "cloud_polling"
    assert manifest["documentation"] == REPO_URL
    assert manifest["issue_tracker"] == ISSUES_URL
    assert manifest["codeowners"] == ["@choucheyu"]
    assert SEMVER_RE.match(manifest["version"]), manifest["version"]


def test_hacs_metadata_matches_taiwan_fork() -> None:
    hacs = _load_json(ROOT / "hacs.json")

    assert hacs["name"] == "Panasonic Smart IoT TW"
    assert hacs["domain"] == "panasonic_ems2"
    assert hacs["documentation"] == REPO_URL
    assert hacs["issue_tracker"] == ISSUES_URL
    assert hacs["render_readme"] is True


def test_translation_files_parse_and_cover_required_sections() -> None:
    translation_dir = INTEGRATION / "translations"
    required_files = {"en.json", "zh-Hant.json"}

    assert required_files.issubset({path.name for path in translation_dir.glob("*.json")})

    for translation_file in sorted(translation_dir.glob("*.json")):
        data = _load_json(translation_file)
        assert "config" in data, translation_file
        assert "options" in data, translation_file
        assert "system_health" in data, translation_file
        assert "user" in data["config"]["step"], translation_file
        assert "init" in data["options"]["step"], translation_file
