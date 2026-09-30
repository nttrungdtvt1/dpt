"""Load experiment configuration from YAML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class LadderSpec:
    name: str
    height: int
    bitrate_kbps: int


@dataclass(frozen=True)
class CandidateSpec:
    height: int
    bitrates_kbps: tuple[int, ...]


@dataclass(frozen=True)
class AppConfig:
    raw: dict[str, Any]
    codec: str
    preset: str
    pixel_format: str
    keyframe_interval_seconds: float
    audio: bool
    two_pass: bool
    fixed_ladder: tuple[LadderSpec, ...]
    candidates: tuple[CandidateSpec, ...]
    complexity: dict[str, Any]
    probe: dict[str, Any]
    quality: dict[str, Any]
    ladder_selection: dict[str, Any]

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT


def default_config_path() -> Path:
    return PROJECT_ROOT / "config" / "config.yaml"


def load_config(path: Path | None = None) -> AppConfig:
    cfg_path = path or default_config_path()
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Khong tim thay file cau hinh: {cfg_path}")
    with cfg_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    ladder = tuple(
        LadderSpec(name=str(item["name"]), height=int(item["height"]), bitrate_kbps=int(item["bitrate_kbps"]))
        for item in data.get("fixed_ladder", [])
    )
    if not ladder:
        raise ValueError("fixed_ladder trong config rong.")
    candidates = tuple(
        CandidateSpec(
            height=int(item["height"]),
            bitrates_kbps=tuple(int(b) for b in item.get("bitrates_kbps") or ()),
        )
        for item in data.get("candidates") or []
    )
    return AppConfig(
        raw=data,
        codec=str(data.get("codec", "libx264")),
        preset=str(data.get("preset", "veryfast")),
        pixel_format=str(data.get("pixel_format", "yuv420p")),
        keyframe_interval_seconds=float(data.get("keyframe_interval_seconds", 2.0)),
        audio=bool(data.get("audio", False)),
        two_pass=bool(data.get("two_pass", False)),
        fixed_ladder=ladder,
        candidates=candidates,
        complexity=dict(data.get("complexity") or {}),
        probe=dict(data.get("probe") or {}),
        quality=dict(data.get("quality") or {}),
        ladder_selection=dict(data.get("ladder_selection") or {}),
    )
