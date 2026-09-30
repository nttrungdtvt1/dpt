"""Read container/stream metadata with FFprobe."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from utils.ffmpeg_tools import FFmpegTools, require_success, run_ffmpeg
from utils.filesystem import require_file


@dataclass(frozen=True)
class VideoMeta:
    path: Path
    width: int
    height: int
    fps: float
    duration_seconds: float
    codec: str | None
    bitrate_bps: int | None
    pix_fmt: str | None
    nb_frames: int | None


def _parse_fps(raw: str | None) -> float:
    if not raw or raw in ("0/0", "N/A"):
        return 0.0
    if "/" in raw:
        num, den = raw.split("/", 1)
        den_f = float(den)
        return float(num) / den_f if den_f else 0.0
    return float(raw)


def probe_video(path: Path, tools: FFmpegTools) -> VideoMeta:
    video_path = require_file(path, "video")
    args = [
        str(tools.ffprobe),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    completed = run_ffmpeg(args, timeout=60)
    require_success(completed, f"FFprobe {video_path.name}")
    payload = json.loads(completed.stdout)
    streams = payload.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError(f"File khong co luong video: {video_path}")
    fmt = payload.get("format") or {}
    duration = float(video.get("duration") or fmt.get("duration") or 0.0)
    bitrate = video.get("bit_rate") or fmt.get("bit_rate")
    nb_frames = video.get("nb_frames")
    return VideoMeta(
        path=video_path,
        width=int(video["width"]),
        height=int(video["height"]),
        fps=_parse_fps(video.get("avg_frame_rate") or video.get("r_frame_rate")),
        duration_seconds=duration,
        codec=video.get("codec_name"),
        bitrate_bps=int(bitrate) if bitrate else None,
        pix_fmt=video.get("pix_fmt"),
        nb_frames=int(nb_frames) if nb_frames and str(nb_frames).isdigit() else None,
    )
