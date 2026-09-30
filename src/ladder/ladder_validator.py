"""Validate ladder constraints used in the report."""

from __future__ import annotations

from analyzer.video_probe import VideoMeta
from config import AppConfig
from ladder.models import LadderRung, validate_ladder

__all__ = ["validate_ladder", "LadderRung"]


def validate(rungs: list[LadderRung], meta: VideoMeta, cfg: AppConfig) -> None:
    validate_ladder(rungs, meta, cfg)
