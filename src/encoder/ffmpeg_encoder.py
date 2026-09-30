"""H.264 encoding through FFmpeg using list arguments only."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from analyzer.video_probe import VideoMeta, probe_video
from config import AppConfig
from ladder.models import LadderRung
from utils.ffmpeg_tools import FFmpegTools, require_success, run_ffmpeg


@dataclass(frozen=True)
class EncodeResult:
    rung: LadderRung
    method: str
    output: Path
    elapsed_seconds: float
    actual_bitrate_kbps: float
    size_bytes: int
    width: int
    height: int


def _gop(meta: VideoMeta, cfg: AppConfig) -> int:
    fps = meta.fps if meta.fps > 1 else 25.0
    gop = int(round(fps * cfg.keyframe_interval_seconds))
    return max(gop, 1)


def _null_sink() -> str:
    return "NUL" if os.name == "nt" else "/dev/null"


def _base_args(tools: FFmpegTools, source: Path, rung: LadderRung, cfg: AppConfig, meta: VideoMeta) -> list[str]:
    gop = _gop(meta, cfg)
    bitrate = f"{rung.bitrate_kbps}k"
    bufsize = f"{rung.bitrate_kbps * 2}k"
    args = [
        str(tools.ffmpeg),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-vf",
        f"scale={rung.width}:{rung.height}:flags=bicubic",
        "-c:v",
        cfg.codec,
        "-preset",
        cfg.preset,
        "-b:v",
        bitrate,
        "-maxrate",
        bitrate,
        "-bufsize",
        bufsize,
        "-g",
        str(gop),
        "-keyint_min",
        str(gop),
        "-sc_threshold",
        "0",
        "-pix_fmt",
        cfg.pixel_format,
    ]
    if not cfg.audio:
        args.append("-an")
    return args


def encode_rung(
    source: Path,
    meta: VideoMeta,
    rung: LadderRung,
    method: str,
    out_dir: Path,
    tools: FFmpegTools,
    cfg: AppConfig,
) -> EncodeResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{source.stem}_{method}_{rung.name}_{rung.bitrate_kbps}k.mp4"
    started = time.perf_counter()
    if cfg.two_pass:
        passlog = out_dir / f"{source.stem}_{method}_{rung.name}_passlog"
        common = _base_args(tools, source, rung, cfg, meta)
        pass1 = common + ["-pass", "1", "-passlogfile", str(passlog), "-f", "mp4", _null_sink()]
        p1 = run_ffmpeg(pass1, timeout=600)
        require_success(p1, f"two-pass 1 {rung.name}")
        pass2 = common + ["-pass", "2", "-passlogfile", str(passlog), str(output)]
        p2 = run_ffmpeg(pass2, timeout=600)
        require_success(p2, f"two-pass 2 {rung.name}")
    else:
        cmd = _base_args(tools, source, rung, cfg, meta) + [str(output)]
        completed = run_ffmpeg(cmd, timeout=600)
        require_success(completed, f"encode {rung.name}")
    elapsed = time.perf_counter() - started
    if not output.is_file() or output.stat().st_size < 100:
        raise RuntimeError(f"File encode khong hop le: {output}")
    encoded_meta = probe_video(output, tools)
    if encoded_meta.bitrate_bps:
        actual = encoded_meta.bitrate_bps / 1000.0
    else:
        actual = (output.stat().st_size * 8 / max(encoded_meta.duration_seconds, 0.001)) / 1000.0
    return EncodeResult(
        rung=rung,
        method=method,
        output=output,
        elapsed_seconds=elapsed,
        actual_bitrate_kbps=actual,
        size_bytes=output.stat().st_size,
        width=encoded_meta.width,
        height=encoded_meta.height,
    )
