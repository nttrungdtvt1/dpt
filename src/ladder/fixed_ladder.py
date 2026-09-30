"""Fixed (content-independent) bitrate ladder."""

from __future__ import annotations

from analyzer.video_probe import VideoMeta
from config import AppConfig
from ladder.models import LadderRung, build_fixed_ladder

__all__ = ["LadderRung", "build_fixed_ladder"]


def build(meta: VideoMeta, cfg: AppConfig) -> list[LadderRung]:
    return build_fixed_ladder(meta, cfg)
