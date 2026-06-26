"""Regression tests that the abandoned SVG camera chart approach is removed."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from tests.helpers.source_parsing import load_constant_assignments

ROOT = Path(__file__).resolve().parents[2]
CONST = ROOT / "custom_components/panasonic_ems2/core/const.py"
MANIFEST = ROOT / "custom_components/panasonic_ems2/manifest.json"
CHART = ROOT / "custom_components/panasonic_ems2/core/chart.py"
CAMERA = ROOT / "custom_components/panasonic_ems2/camera.py"
TEMPLATE = ROOT / "dashboard_template.yaml"


def test_svg_camera_chart_entities_are_not_forwarded() -> None:
    constants = load_constant_assignments(CONST)

    assert "camera" not in constants["DOMAINS"]
    assert not CAMERA.exists()
    assert not CHART.exists()


def test_user_info_statistics_declares_recorder_dependency() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert "recorder" in manifest.get("dependencies", [])


def test_panasonic_statistics_dashboard_template_uses_official_statistics_graph() -> None:
    template = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))

    assert template["title"] == "Panasonic 統計圖表"
    assert template["type"] == "sections"
    assert template["max_columns"] == 2

    sections = template["sections"]
    assert [section["cards"][0]["heading"] for section in sections] == [
        "用電量 - 近 30 日（日統計）",
        "用電量 - 近 12 個月（月統計）",
        "洗衣機用水量 - 近 30 日（日統計）",
        "洗衣機用水量 - 近 12 個月（月統計）",
        "洗衣機洗衣次數 - 近 30 日（日統計）",
        "洗衣機洗衣次數 - 近 12 個月（月統計）",
    ]

    graphs = [section["cards"][1] for section in sections]
    assert [graph["period"] for graph in graphs] == ["day", "month", "day", "month", "day", "month"]
    assert all(graph["type"] == "statistics-graph" for graph in graphs)
    assert all("title" not in graph for graph in graphs)
    assert all(graph["stat_types"] == ["state"] for graph in graphs)
    assert all(graph["chart_type"] == "bar" for graph in graphs)
