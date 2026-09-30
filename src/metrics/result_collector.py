"""Collect experiment rows and export CSV/JSON."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from encoder.ffmpeg_encoder import EncodeResult
from metrics.quality_metrics import QualityScores


@dataclass
class ExperimentRow:
    video: str
    method: str
    rung: str
    width: int
    height: int
    target_bitrate_kbps: int
    actual_bitrate_kbps: float
    size_bytes: int
    encode_seconds: float
    psnr: float | None
    ssim: float | None
    vmaf: float | None
    vmaf_min: float | None
    vmaf_max: float | None
    complexity_label: str
    complexity_index: float
    k: float
    output_file: str


def row_from(
    video_name: str,
    encode: EncodeResult,
    quality: QualityScores | None,
    label: str,
    index: float,
    k: float,
    method: str | None = None,
) -> ExperimentRow:
    return ExperimentRow(
        video=video_name,
        method=method or encode.method,
        rung=encode.rung.name,
        width=encode.width,
        height=encode.height,
        target_bitrate_kbps=encode.rung.bitrate_kbps,
        actual_bitrate_kbps=round(encode.actual_bitrate_kbps, 3),
        size_bytes=encode.size_bytes,
        encode_seconds=round(encode.elapsed_seconds, 3),
        psnr=None if quality is None else quality.psnr_average,
        ssim=None if quality is None else quality.ssim_all,
        vmaf=None if quality is None else quality.vmaf,
        vmaf_min=None if quality is None else quality.vmaf_min,
        vmaf_max=None if quality is None else quality.vmaf_max,
        complexity_label=label,
        complexity_index=round(index, 4),
        k=k,
        output_file=str(encode.output),
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[ExperimentRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Khong co dong ket qua de ghi CSV.")
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
