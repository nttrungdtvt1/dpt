"""Combine metadata, complexity, and optional CRF probe."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analyzer.complexity import ComplexityResult, analyze_complexity
from analyzer.video_probe import VideoMeta, probe_video
from config import AppConfig
from utils.ffmpeg_tools import FFmpegTools, require_success, run_ffmpeg


@dataclass(frozen=True)
class VideoFeatures:
    meta: VideoMeta
    complexity: ComplexityResult
    probe_bitrate_kbps: float | None
    adjusted_k: float
    adjusted_label: str


def _crf_probe_bitrate(meta: VideoMeta, tools: FFmpegTools, cfg: AppConfig, work_dir: Path) -> float:
    duration = float(cfg.probe.get("duration_seconds", 8))
    crf = int(cfg.probe.get("crf", 23))
    out = work_dir / f"{meta.path.stem}_crf_probe.mp4"
    args = [
        str(tools.ffmpeg),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(meta.path),
        "-t",
        str(duration),
        "-c:v",
        cfg.codec,
        "-preset",
        cfg.preset,
        "-crf",
        str(crf),
        "-an",
        str(out),
    ]
    completed = run_ffmpeg(args, timeout=300)
    require_success(completed, "CRF probe")
    probed = probe_video(out, tools)
    if not probed.bitrate_bps:
        size = out.stat().st_size
        if probed.duration_seconds <= 0:
            raise RuntimeError("CRF probe khong do duoc bitrate.")
        return (size * 8 / probed.duration_seconds) / 1000.0
    return probed.bitrate_bps / 1000.0


def extract_features(
    path: Path,
    tools: FFmpegTools,
    cfg: AppConfig,
    work_dir: Path | None = None,
) -> VideoFeatures:
    meta = probe_video(path, tools)
    if meta.width < 16 or meta.height < 16:
        raise ValueError(f"Do phan giai qua nho: {meta.width}x{meta.height}")
    if meta.duration_seconds <= 0.2:
        raise ValueError(f"Video qua ngan: {meta.duration_seconds:.3f}s")
    complexity = analyze_complexity(meta, tools, cfg)
    probe_br = None
    k = complexity.k
    label = complexity.label
    if bool(cfg.probe.get("enabled", False)):
        if work_dir is None:
            raise ValueError("Can work_dir khi bat CRF probe.")
        probe_br = _crf_probe_bitrate(meta, tools, cfg, work_dir)
        # Probe bitrate cao hon nguong -> noi dung kho nen hon nhan SI/TI.
        if probe_br >= 2500 and label != "hard":
            label, k = "hard", float(cfg.complexity.get("k_hard", 1.35))
        elif probe_br <= 800 and label != "easy":
            label, k = "easy", float(cfg.complexity.get("k_easy", 0.65))
    return VideoFeatures(
        meta=meta,
        complexity=complexity,
        probe_bitrate_kbps=probe_br,
        adjusted_k=k,
        adjusted_label=label,
    )
