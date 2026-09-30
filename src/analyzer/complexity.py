"""Spatial/Temporal complexity estimates inspired by ITU-T P.910 SI/TI.

This is an approximation for student experiments, not a certified P.910
implementation. Median aggregation is used instead of max to reduce the
effect of a single scene cut.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import AppConfig
from utils.ffmpeg_tools import FFmpegTools
from analyzer.video_probe import VideoMeta


@dataclass(frozen=True)
class ComplexityResult:
    si: float
    ti: float
    index: float
    label: str
    k: float
    frames_used: int


def sobel_magnitude(gray: np.ndarray) -> np.ndarray:
    img = gray.astype(np.float64)
    gx = (
        -img[:-2, :-2]
        - 2 * img[1:-1, :-2]
        - img[2:, :-2]
        + img[:-2, 2:]
        + 2 * img[1:-1, 2:]
        + img[2:, 2:]
    )
    gy = (
        -img[:-2, :-2]
        - 2 * img[:-2, 1:-1]
        - img[:-2, 2:]
        + img[2:, :-2]
        + 2 * img[2:, 1:-1]
        + img[2:, 2:]
    )
    return np.hypot(gx, gy)


def spatial_information(gray: np.ndarray) -> float:
    mag = sobel_magnitude(gray)
    if mag.size == 0:
        return 0.0
    return float(np.std(mag))


def temporal_information(prev: np.ndarray, curr: np.ndarray) -> float:
    diff = curr.astype(np.float64) - prev.astype(np.float64)
    return float(np.std(diff))


def classify_complexity(index: float, cfg: AppConfig) -> tuple[str, float]:
    easy_max = float(cfg.complexity.get("easy_max", 0.35))
    hard_min = float(cfg.complexity.get("hard_min", 0.65))
    if index < easy_max:
        return "easy", float(cfg.complexity.get("k_easy", 0.65))
    if index >= hard_min:
        return "hard", float(cfg.complexity.get("k_hard", 1.35))
    return "medium", float(cfg.complexity.get("k_medium", 1.0))


def complexity_index(si: float, ti: float, cfg: AppConfig) -> float:
    si_ref = float(cfg.complexity.get("si_ref", 80.0))
    ti_ref = float(cfg.complexity.get("ti_ref", 40.0))
    value = 0.55 * (si / si_ref) + 0.45 * (ti / ti_ref)
    return float(np.clip(value, 0.0, 1.5))


def extract_gray_frames(meta: VideoMeta, tools: FFmpegTools, cfg: AppConfig) -> np.ndarray:
    """Decode sampled grayscale frames through FFmpeg stdout (binary)."""
    import subprocess

    width = int(cfg.complexity.get("analysis_width", 320))
    width = width - (width % 2)
    sample_fps = float(cfg.complexity.get("sample_fps", 2.0))
    max_frames = int(cfg.complexity.get("max_frames", 40))
    height = max(2, int(round(meta.height * width / meta.width)))
    height = height - (height % 2)
    vf = f"fps={sample_fps},format=gray,scale={width}:{height}"
    args = [
        str(tools.ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(meta.path),
        "-vf",
        vf,
        "-vframes",
        str(max_frames),
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    completed = subprocess.run(args, capture_output=True, check=False, shell=False)
    if completed.returncode != 0:
        err = completed.stderr.decode("utf-8", errors="replace")[-1500:]
        raise RuntimeError(f"Khong trich duoc khung hinh tu {meta.path.name}.\n{err}")
    frame_size = width * height
    if frame_size <= 0:
        raise ValueError("Kich thuoc khung phan tich khong hop le.")
    buf = completed.stdout
    n_frames = len(buf) // frame_size
    if n_frames < 2:
        raise RuntimeError(f"Video qua ngan de tinh TI: {meta.path.name}")
    frames = np.frombuffer(buf, dtype=np.uint8, count=n_frames * frame_size)
    return frames.reshape((n_frames, height, width))


def analyze_complexity(meta: VideoMeta, tools: FFmpegTools, cfg: AppConfig) -> ComplexityResult:
    frames = extract_gray_frames(meta, tools, cfg)
    si_vals = [spatial_information(frame) for frame in frames]
    ti_vals = [temporal_information(frames[i - 1], frames[i]) for i in range(1, len(frames))]
    
    # Theo huong dan: lay gia tri cuc dai theo thoi gian de dac trung do phuc tap cua doan kho nhat
    si = float(np.max(si_vals)) if si_vals else 0.0
    ti = float(np.max(ti_vals)) if ti_vals else 0.0
    
    index = complexity_index(si, ti, cfg)
    label, k = classify_complexity(index, cfg)
    return ComplexityResult(si=si, ti=ti, index=index, label=label, k=k, frames_used=len(frames))

