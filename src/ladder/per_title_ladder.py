"""Content-aware bitrate ladder selection at experimental level.

build_per_title_ladder(k) remains the heuristic baseline (k × fixed).
The main proposed method is select_ladder_from_hull in ladder.models.
"""

from __future__ import annotations

from analyzer.video_probe import VideoMeta
from config import AppConfig
from ladder.models import LadderRung, build_per_title_ladder

__all__ = ["build_per_title_ladder", "LadderRung"]


def build(meta: VideoMeta, cfg: AppConfig, k: float) -> list[LadderRung]:
    return build_per_title_ladder(meta, cfg, k)
