"""Full-reference quality metrics via FFmpeg filters.

VMAF (libvmaf) is the primary metric when quality.vmaf is true.
PSNR and SSIM remain available as secondary metrics. Missing VMAF is an
error when the flag is on; scores are never invented.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from analyzer.video_probe import VideoMeta
from config import AppConfig
from utils.ffmpeg_tools import FFmpegTools, run_ffmpeg


def ffmpeg_has_libvmaf(tools: FFmpegTools) -> bool:
    """True when this FFmpeg build exposes the libvmaf filter."""
    completed = run_ffmpeg([str(tools.ffmpeg), "-hide_banner", "-filters"], timeout=30)
    text = f"{completed.stdout or ''}{completed.stderr or ''}".lower()
    return "libvmaf" in text


@dataclass(frozen=True)
class QualityScores:
    psnr_average: float | None
    ssim_all: float | None
    vmaf: float | None
    vmaf_min: float | None
    vmaf_max: float | None
    notes: str


_PSNR_RE = re.compile(r"average:([0-9.]+)")
_SSIM_RE = re.compile(r"All:([0-9.]+)")
_VMAF_RE = re.compile(r"VMAF score:\s*([0-9.]+)", re.I)


def parse_vmaf_score(text: str) -> float | None:
    """Parse the average VMAF line emitted by FFmpeg libvmaf."""
    match = _VMAF_RE.search(text or "")
    return float(match.group(1)) if match else None


def _run_filter(tools: FFmpegTools, encoded: Path, reference: Path, width: int, height: int, filter_name: str) -> str:
    filt = (
        f"[0:v]scale={width}:{height}:flags=bicubic,setsar=1[d];"
        f"[1:v]setsar=1[r];[d][r]{filter_name}"
    )
    args = [
        str(tools.ffmpeg),
        "-hide_banner",
        "-i",
        str(encoded),
        "-i",
        str(reference),
        "-filter_complex",
        filt,
        "-f",
        "null",
        "-",
    ]
    completed = run_ffmpeg(args, timeout=300)
    return (completed.stderr or "") + (completed.stdout or "")


def measure_quality(
    encoded: Path,
    reference: Path,
    source_meta: VideoMeta,
    tools: FFmpegTools,
    cfg: AppConfig,
) -> QualityScores:
    notes: list[str] = []
    psnr_val = None
    ssim_val = None
    vmaf_val = None
    vmaf_min = None
    vmaf_max = None
    width, height = source_meta.width, source_meta.height
    if cfg.quality.get("psnr", True):
        text = _run_filter(tools, encoded, reference, width, height, "psnr")
        match = _PSNR_RE.search(text)
        if not match:
            raise RuntimeError(f"Khong parse duoc PSNR cho {encoded.name}.\n{text[-800:]}")
        psnr_val = float(match.group(1))
    if cfg.quality.get("ssim", True):
        text = _run_filter(tools, encoded, reference, width, height, "ssim")
        match = _SSIM_RE.search(text)
        if not match:
            raise RuntimeError(f"Khong parse duoc SSIM cho {encoded.name}.\n{text[-800:]}")
        ssim_val = float(match.group(1))
    if cfg.quality.get("vmaf", False):
        model = str(cfg.quality.get("vmaf_model", "version=vmaf_v0.6.1"))
        # Tao ten file log tam thoi trong cung thu muc
        vmaf_log_path = encoded.with_name(f"{encoded.stem}_vmaf.json")
        # Path phai replace backslash tren Windows thanh forward slash, va escape dau ":" de FFmpeg hieu dung
        safe_log_path = str(vmaf_log_path.absolute()).replace('\\', '/').replace(':', r'\:')
        
        vmaf_filter = f"libvmaf=model={model}:log_path='{safe_log_path}':log_fmt=json:n_threads=4"
        text = _run_filter(tools, encoded, reference, width, height, vmaf_filter)
        
        # Doc json de lay min, max
        if vmaf_log_path.is_file():
            try:
                with vmaf_log_path.open("r", encoding="utf-8") as f:
                    log_data = json.load(f)
                frames = log_data.get("frames", [])
                metrics = [f.get("metrics", {}).get("vmaf") for f in frames]
                valid_metrics = [m for m in metrics if m is not None]
                if valid_metrics:
                    vmaf_min = min(valid_metrics)
                    vmaf_max = max(valid_metrics)
                    # VMAF co the tu tinh trung binh, hoac lay tu pooled_metrics
                    pooled = log_data.get("pooled_metrics", {}).get("vmaf")
                    if pooled and pooled.get("mean") is not None:
                        vmaf_val = pooled.get("mean")
                    else:
                        vmaf_val = sum(valid_metrics) / len(valid_metrics)
            except Exception as e:
                notes.append(f"Khong the doc VMAF log: {e}")
            finally:
                # Xoa file log sau khi doc xong
                try:
                    vmaf_log_path.unlink()
                except OSError:
                    pass
        
        if vmaf_val is None:
            # Fallback ve cach parse stdout cu neu co loi ghi file
            vmaf_val = parse_vmaf_score(text)
            
        if vmaf_val is None:
            raise RuntimeError(
                f"VMAF bat nhung khong lay duoc diem cho {encoded.name}. "
                f"Kiem tra libvmaf va model '{model}'.\n{text[-1200:]}"
            )
        notes.append(f"VMAF model={model}")
    else:
        notes.append("VMAF tat. Dung PSNR/SSIM.")
    return QualityScores(
        psnr_average=psnr_val,
        ssim_all=ssim_val,
        vmaf=vmaf_val,
        vmaf_min=vmaf_min,
        vmaf_max=vmaf_max,
        notes="; ".join(notes)
    )
