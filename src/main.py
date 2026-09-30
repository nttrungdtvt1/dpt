"""CLI for the per-title VOD encoding demo."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import default_config_path, load_config
from pipeline import run_pipeline
from utils.ffmpeg_tools import find_ffmpeg_tools, run_ffmpeg
from utils.logger import setup_logging
from utils.sample_video import make_sample_video
from metrics.quality_metrics import ffmpeg_has_libvmaf


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Content-aware bitrate ladder selection (experimental) cho VOD.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Vi du: python src/main.py run data/samples/testsrc2_720p.mp4 --output results",
    )
    parser.add_argument("--config", type=Path, default=None, help="Duong dan config YAML")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "check-env",
        help="Kiem tra FFmpeg/FFprobe/libvmaf va trang thai moi truong",
    )

    sample = sub.add_parser("make-sample", help="Tao video mau ngan bang FFmpeg lavfi")
    sample.add_argument("--output", type=Path, default=Path("data/samples/sample_testsrc.mp4"))
    sample.add_argument("--seconds", type=float, default=15.0,
                        help="Do dai video (khuyen nghi 10-30s)")
    sample.add_argument("--size", default="1280x720")
    sample.add_argument("--pattern", default="testsrc2",
                        choices=["testsrc", "testsrc2", "smptebars"])

    analyze = sub.add_parser(
        "analyze",
        help="Phan tich video (FFprobe + SI/TI + candidate space) khong encode",
    )
    analyze.add_argument("videos", nargs="+", type=Path)

    encode_sub = sub.add_parser(
        "encode",
        help="Chi encode candidates (khong VMAF, nhanh hon cho kiem tra encoding)",
    )
    encode_sub.add_argument("videos", nargs="+", type=Path)
    encode_sub.add_argument("--output", type=Path, default=Path("results"),
                            help="Thu muc output")

    evaluate_sub = sub.add_parser(
        "evaluate",
        help="Chay toan bo pipeline va tao bao cao (giong run)",
    )
    evaluate_sub.add_argument("videos", nargs="+", type=Path)
    evaluate_sub.add_argument("--output", type=Path, default=Path("results"),
                              help="Thu muc output")

    run = sub.add_parser(
        "run",
        help="Chay toan bo pipeline: probe → SI/TI → encode → VMAF → Pareto → ladder → report",
    )
    run.add_argument("videos", nargs="+", type=Path)
    run.add_argument("--output", type=Path, default=Path("results"), help="Thu muc output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logger = setup_logging(logging.INFO)
    try:
        tools = find_ffmpeg_tools()
    except Exception as exc:
        logger.error("%s", exc)
        return 2

    if args.command == "check-env":
        print(f"=== Kiem tra moi truong ===")
        print(f"ffmpeg : {tools.ffmpeg}")
        print(f"ffprobe: {tools.ffprobe}")
        # Lay version FFmpeg
        ver_result = run_ffmpeg([str(tools.ffmpeg), "-hide_banner", "-version"], timeout=15)
        ver_line = (ver_result.stdout or ver_result.stderr or "").split("\n")[0].strip()
        print(f"version: {ver_line}")
        # Kiem tra libvmaf
        has_vmaf = ffmpeg_has_libvmaf(tools)
        status = "CO" if has_vmaf else "KHONG CO"
        print(f"libvmaf: {status}")
        if not has_vmaf:
            print()
            print("[CANH BAO] FFmpeg khong co libvmaf. Can cai dat FFmpeg full_build.")
            print("Tren Windows: winget install --id Gyan.FFmpeg -e (full_build)")
            return 1
        print()
        print("[OK] Moi truong san sang. Chay: python src/main.py run <video>")
        return 0

    cfg = load_config(args.config or default_config_path())

    if args.command == "make-sample":
        path = make_sample_video(tools, args.output, seconds=args.seconds, size=args.size, pattern=args.pattern)
        print(path)
        return 0

    if args.command == "analyze":
        from analyzer.feature_extractor import extract_features
        from ladder.models import (
            build_candidate_rungs,
            build_fixed_ladder,
            build_per_title_ladder,
            validate_ladder,
        )

        for video in args.videos:
            features = extract_features(video, tools, cfg, work_dir=Path("results") / "work")
            fixed = build_fixed_ladder(features.meta, cfg)
            per_title = build_per_title_ladder(features.meta, cfg, features.adjusted_k)
            validate_ladder(fixed, features.meta, cfg)
            validate_ladder(per_title, features.meta, cfg)
            candidates = build_candidate_rungs(features.meta, cfg) if cfg.candidates else []
            print(
                json.dumps(
                    {
                        "video": str(video),
                        "size": f"{features.meta.width}x{features.meta.height}",
                        "fps": features.meta.fps,
                        "duration": features.meta.duration_seconds,
                        "si": features.complexity.si,
                        "ti": features.complexity.ti,
                        "label": features.adjusted_label,
                        "k": features.adjusted_k,
                        "note": "SI/TI mo ta do phuc tap; hull ladder can encode+VMAF (lenh run).",
                        "candidates": [item.__dict__ for item in candidates],
                        "fixed": [item.__dict__ for item in fixed],
                        "per_title": [item.__dict__ for item in per_title],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return 0

    if args.command == "encode":
        # Chi encode candidates, khong tinh VMAF de kiem tra nhanh
        from analyzer.feature_extractor import extract_features
        from encoder.ffmpeg_encoder import encode_rung
        from ladder.models import build_candidate_rungs
        from utils.filesystem import ensure_dir

        output_dir = ensure_dir(args.output)
        for video in args.videos:
            video = Path(video)
            if not video.is_file():
                logger.error("Video khong ton tai: %s", video)
                continue
            features = extract_features(video, tools, cfg, work_dir=output_dir / "work")
            meta = features.meta
            candidates = build_candidate_rungs(meta, cfg)
            out_dir = ensure_dir(output_dir / "encodes" / video.stem / "candidate")
            for ci, rung in enumerate(candidates, 1):
                print(f"[{ci}/{len(candidates)}] Encode {rung.name} @ {rung.bitrate_kbps} kbps...", flush=True)
                result = encode_rung(video, meta, rung, "candidate", out_dir, tools, cfg)
                print(f"    → {result.output.name} | actual: {result.actual_bitrate_kbps:.1f} kbps | {result.size_bytes // 1024} KB")
        return 0

    if args.command in ("run", "evaluate"):
        summary = run_pipeline(args.videos, args.output, tools, cfg)
        # In summary gon
        print(json.dumps(
            {
                k: v for k, v in summary.items() if k != "analyses"
            },
            indent=2,
            ensure_ascii=False,
        ))
        return 0

    logger.error("Lenh khong ho tro: %s", args.command)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
