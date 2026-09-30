"""End-to-end per-title vs fixed ladder pipeline.

Scientific order:

    Video → FFprobe → SI/TI (content complexity, not ladder selection)
         → Candidate grid → FFmpeg encode → VMAF (+ PSNR/SSIM)
         → bitrate–VMAF dataset → remove dominated → Pareto
         → upper convex hull → hull-based ladder selection
         → Fixed ladder + heuristic k×fixed baselines → compare

SI/TI still produce k for the heuristic baseline only.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from analysis.rq_points import RQPoint, pareto_frontier, upper_convex_hull
from analyzer.feature_extractor import extract_features
from config import AppConfig
from encoder.ffmpeg_encoder import EncodeResult, encode_rung
from ladder.models import (
    LadderRung,
    build_candidate_rungs,
    build_fixed_ladder,
    build_per_title_ladder,
    select_ladder_from_hull,
    validate_ladder,
)
from metrics.quality_metrics import QualityScores, measure_quality
from metrics.result_collector import ExperimentRow, row_from, write_csv, write_json
from report import build_report, write_pareto_csv, write_proposed_ladder_csv
from utils.ffmpeg_tools import FFmpegTools
from utils.filesystem import ensure_dir, require_file, safe_stem
from visualization.plots import plot_results

logger = logging.getLogger("per_title")


class _Progress:
    """Simple progress indicator [step/total] logged to console."""

    def __init__(self, total: int) -> None:
        self.total = total
        self._step = 0

    def next(self, msg: str) -> None:
        self._step += 1
        prefix = f"[{self._step}/{self.total}]"
        print(f"{prefix} {msg}", flush=True)
        logger.info("%s %s", prefix, msg)


def _rq_point(row: ExperimentRow) -> RQPoint:
    if row.vmaf is None:
        raise RuntimeError(
            f"Thieu VMAF cho {row.video} {row.rung}. Bat quality.vmaf va dam bao libvmaf chay that."
        )
    return RQPoint(
        bitrate_kbps=float(row.actual_bitrate_kbps),
        vmaf=float(row.vmaf),
        width=row.width,
        height=row.height,
        target_bitrate_kbps=row.target_bitrate_kbps,
        rung_name=row.rung,
        size_bytes=row.size_bytes,
        encode_seconds=row.encode_seconds,
        psnr=row.psnr,
        ssim=row.ssim,
        output_file=row.output_file,
    )


def _encode_and_score(
    video: Path,
    meta: Any,
    rung: LadderRung,
    method: str,
    out_dir: Path,
    tools: FFmpegTools,
    cfg: AppConfig,
    cache: dict[tuple[int, int], tuple[EncodeResult, QualityScores]],
) -> tuple[EncodeResult, QualityScores]:
    key = (rung.height, rung.bitrate_kbps)
    cached = cache.get(key)
    if cached is not None:
        return cached
    encoded = encode_rung(video, meta, rung, method, out_dir, tools, cfg)
    quality = measure_quality(encoded.output, video, meta, tools, cfg)
    cache[key] = (encoded, quality)
    return encoded, quality


def _points_payload(points: list[RQPoint]) -> list[dict[str, Any]]:
    return [asdict(point) for point in points]


def _write_bitrate_vmaf_csv(path: Path, rows: list[ExperimentRow]) -> None:
    candidates = [row for row in rows if row.method == "candidate"]
    if not candidates:
        raise ValueError("Khong co candidate nao de ghi bitrate_vmaf.csv.")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "video",
        "resolution",
        "width",
        "height",
        "target_bitrate_kbps",
        "bitrate_kbps",
        "vmaf",
        "vmaf_min",
        "vmaf_max",
        "psnr",
        "ssim",
        "size_bytes",
        "encode_seconds",
        "rung",
        "output_file",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in candidates:
            writer.writerow(
                {
                    "video": row.video,
                    "resolution": f"{row.height}p",
                    "width": row.width,
                    "height": row.height,
                    "target_bitrate_kbps": row.target_bitrate_kbps,
                    "bitrate_kbps": row.actual_bitrate_kbps,
                    "vmaf": row.vmaf,
                    "vmaf_min": row.vmaf_min,
                    "vmaf_max": row.vmaf_max,
                    "psnr": row.psnr,
                    "ssim": row.ssim,
                    "size_bytes": row.size_bytes,
                    "encode_seconds": row.encode_seconds,
                    "rung": row.rung,
                    "output_file": row.output_file,
                }
            )


def run_pipeline(
    videos: list[Path],
    output_dir: Path,
    tools: FFmpegTools,
    cfg: AppConfig,
) -> dict[str, Any]:
    if not videos:
        raise ValueError("Chua cung cap video dau vao.")
    if not bool(cfg.quality.get("vmaf", False)):
        raise RuntimeError(
            "Pipeline hull-based can VMAF that. Bat quality.vmaf trong config; khong dung so lieu gia."
        )
    n_videos = len(videos)
    # Uoc tinh so buoc: check + probe + siti + candidates(encode+vmaf) + ladders + pareto + report
    # Moi video: 3 phase chinh (encode candidates, encode ladders, postprocess)
    total_steps = 3 + n_videos * 4 + 2  # approximate
    prog = _Progress(total_steps)

    prog.next("Kiem tra moi truong va dau vao...")
    output_dir = ensure_dir(output_dir)
    encodes_dir = ensure_dir(output_dir / "encodes")
    work_dir = ensure_dir(output_dir / "work")
    plots_dir = ensure_dir(output_dir / "plots")
    report_dir = ensure_dir(output_dir / "report")

    rows: list[ExperimentRow] = []
    analyses: list[dict[str, Any]] = []

    for i_vid, raw in enumerate(videos, 1):
        video = require_file(raw, "video")
        prog.next(f"FFprobe + SI/TI: {video.name} ({i_vid}/{n_videos})")
        features = extract_features(video, tools, cfg, work_dir=work_dir)
        meta = features.meta
        # Duration warning
        dur = meta.duration_seconds
        if dur < 10 or dur > 30:
            logger.warning(
                "Video %s: duration=%.1fs nam ngoai khoang khuyen nghi 10-30s. Pipeline van tiep tuc.",
                video.name, dur,
            )
            print(f"  [CANH BAO] {video.name}: duration={dur:.1f}s (khuyen nghi 10-30s)", flush=True)
        k = features.adjusted_k
        label = features.adjusted_label
        stem = safe_stem(video)

        prog.next(f"Encode candidates: {video.name} ({i_vid}/{n_videos})")
        candidates = build_candidate_rungs(meta, cfg)
        cache: dict[tuple[int, int], tuple[EncodeResult, QualityScores]] = {}
        candidate_dir = ensure_dir(encodes_dir / stem / "candidate")
        candidate_rows: list[ExperimentRow] = []
        for ci, rung in enumerate(candidates, 1):
            logger.info(
                "Encode %s candidate %d/%d %s @ %s kbps",
                video.name, ci, len(candidates), rung.name, rung.bitrate_kbps,
            )
            print(f"    Candidate {ci}/{len(candidates)}: {rung.name} @ {rung.bitrate_kbps} kbps", flush=True)
            encoded, quality = _encode_and_score(
                video, meta, rung, "candidate", candidate_dir, tools, cfg, cache
            )
            row = row_from(video.name, encoded, quality, label, features.complexity.index, k, method="candidate")
            rows.append(row)
            candidate_rows.append(row)

        prog.next(f"Pareto + Hull + Ladder selection: {video.name} ({i_vid}/{n_videos})")
        rq_points = [_rq_point(row) for row in candidate_rows]
        pareto = pareto_frontier(rq_points)
        hull = upper_convex_hull(pareto)
        hull_ladder = select_ladder_from_hull(hull, meta, cfg)
        validate_ladder(hull_ladder, meta, cfg)
        print(f"    Pareto: {len(pareto)} diem | Hull: {len(hull)} diem | Ladder: {len(hull_ladder)} bac", flush=True)

        fixed = build_fixed_ladder(meta, cfg)
        heuristic = build_per_title_ladder(meta, cfg, k)
        validate_ladder(fixed, meta, cfg)
        validate_ladder(heuristic, meta, cfg)

        prog.next(f"Encode ladders (hull/fixed/heuristic): {video.name} ({i_vid}/{n_videos})")
        ladders = (
            ("hull", hull_ladder, ensure_dir(encodes_dir / stem / "hull")),
            ("fixed", fixed, ensure_dir(encodes_dir / stem / "fixed")),
            ("per_title", heuristic, ensure_dir(encodes_dir / stem / "per_title")),
        )
        for method, ladder, method_dir in ladders:
            for li, rung in enumerate(ladder, 1):
                logger.info(
                    "Encode %s %s %d/%d %s @ %s kbps",
                    video.name, method, li, len(ladder), rung.name, rung.bitrate_kbps,
                )
                encoded, quality = _encode_and_score(
                    video, meta, rung, method, method_dir, tools, cfg, cache
                )
                rows.append(
                    row_from(
                        video.name,
                        encoded,
                        quality,
                        label,
                        features.complexity.index,
                        k,
                        method=method,
                    )
                )

        analyses.append(
            {
                "video": video.name,
                "width": meta.width,
                "height": meta.height,
                "fps": meta.fps,
                "duration_seconds": meta.duration_seconds,
                "source_codec": meta.codec,
                "source_bitrate_bps": meta.bitrate_bps,
                "si": features.complexity.si,
                "ti": features.complexity.ti,
                "complexity_index": features.complexity.index,
                "complexity_label": label,
                "k": k,
                "content_complexity_role": (
                    "SI/TI mo ta do phuc tap noi dung de doi chieu cac duong bitrate-VMAF; "
                    "k chi dung cho heuristic baseline (k x fixed), khong chon ladder chinh."
                ),
                "probe_bitrate_kbps": features.probe_bitrate_kbps,
                "candidates": [asdict(rung) for rung in candidates],
                "rq_points": _points_payload(rq_points),
                "pareto": _points_payload(pareto),
                "convex_hull": _points_payload(hull),
                "hull_ladder": [asdict(rung) for rung in hull_ladder],
                "fixed_ladder": [asdict(rung) for rung in fixed],
                "per_title_ladder": [asdict(rung) for rung in heuristic],
                "methods": {
                    "fixed": "content-independent baseline",
                    "per_title": "heuristic baseline k x fixed ladder",
                    "hull": "hull-based per-title ladder selection",
                },
            }
        )

    prog.next("Luu CSV, JSON va ve bieu do...")
    csv_path = output_dir / "experiment_results.csv"
    json_path = output_dir / "experiment_results.json"
    vmaf_csv_path = output_dir / "bitrate_vmaf.csv"
    pareto_csv_path = output_dir / "pareto.csv"
    proposed_csv_path = output_dir / "proposed_ladder.csv"
    write_csv(csv_path, rows)
    _write_bitrate_vmaf_csv(vmaf_csv_path, rows)
    write_pareto_csv(analyses, pareto_csv_path)
    write_proposed_ladder_csv(analyses, proposed_csv_path)
    payload = {
        "disclaimer": (
            "Day la ket qua thu nghiem: ladder hull-based duoc chon tu upper convex hull "
            "cua tap Pareto bitrate-VMAF, khong phai toi uu toan cuc. "
            "Pareto frontier khong dong nghia voi convex hull. "
            "build_per_title_ladder(k) chi la heuristic baseline."
        ),
        "pipeline": [
            "FFprobe",
            "SI/TI content complexity",
            "candidate encoding grid",
            "FFmpeg encode",
            "VMAF (+ PSNR/SSIM)",
            "bitrate-VMAF dataset",
            "remove dominated points",
            "Pareto frontier",
            "upper convex hull",
            "hull-based ladder selection",
            "fixed ladder baseline",
            "heuristic k x fixed baseline",
            "compare",
        ],
        "analyses": analyses,
        "rows": [asdict(row) for row in rows],
    }
    write_json(json_path, payload)
    plot_files = plot_results(rows, plots_dir, analyses=analyses)

    prog.next("Tao bao cao Markdown...")
    report_path = report_dir / "results.md"
    build_report(analyses, [asdict(row) for row in rows], report_path)

    print(f"\n=== PIPELINE HOAN THANH ===", flush=True)
    print(f"Output: {output_dir}", flush=True)
    print(f"Report: {report_path}", flush=True)
    print(f"Bieu do: {plots_dir}", flush=True)

    return {
        "output_dir": str(output_dir),
        "csv": str(csv_path),
        "json": str(json_path),
        "bitrate_vmaf_csv": str(vmaf_csv_path),
        "pareto_csv": str(pareto_csv_path),
        "proposed_ladder_csv": str(proposed_csv_path),
        "report": str(report_path),
        "plots": [str(path) for path in plot_files],
        "row_count": len(rows),
        "analyses": analyses,
    }
