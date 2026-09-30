"""Ladder data types, fixed baseline, per-title adjustment, and validation."""

from __future__ import annotations

from dataclasses import dataclass

from analysis.rq_points import RQPoint
from analyzer.video_probe import VideoMeta
from config import AppConfig, LadderSpec


@dataclass(frozen=True)
class LadderRung:
    name: str
    width: int
    height: int
    bitrate_kbps: int
    source: str


def even(value: int) -> int:
    return value if value % 2 == 0 else value - 1


def size_for_height(meta: VideoMeta, target_height: int) -> tuple[int, int]:
    height = even(min(target_height, meta.height))
    if height < 2:
        raise ValueError("Chieu cao ladder khong hop le.")
    width = even(int(round(meta.width * height / meta.height)))
    width = max(width, 2)
    return width, height


def materialize(spec: LadderSpec, meta: VideoMeta, source: str) -> LadderRung | None:
    if spec.height > meta.height:
        return None
    width, height = size_for_height(meta, spec.height)
    return LadderRung(
        name=spec.name,
        width=width,
        height=height,
        bitrate_kbps=int(spec.bitrate_kbps),
        source=source,
    )


def build_fixed_ladder(meta: VideoMeta, cfg: AppConfig) -> list[LadderRung]:
    rungs: list[LadderRung] = []
    for spec in cfg.fixed_ladder:
        rung = materialize(spec, meta, "fixed")
        if rung is not None:
            rungs.append(rung)
    if not rungs:
        raise ValueError("Khong con bac ladder nao phu hop voi do phan giai nguon.")
    return rungs


def round_bitrate(value: float, step: int) -> int:
    if step <= 0:
        return int(round(value))
    return int(max(step, round(value / step) * step))


def build_per_title_ladder(meta: VideoMeta, cfg: AppConfig, k: float) -> list[LadderRung]:
    """Heuristic baseline: scale the fixed ladder by complexity factor k.

    This is NOT hull-based selection. Kept for comparison with
    select_ladder_from_hull.
    """
    step = int(cfg.complexity.get("bitrate_step_kbps", 50))
    min_br = int(cfg.complexity.get("min_bitrate_kbps", 150))
    max_br = int(cfg.complexity.get("max_bitrate_kbps", 8000))
    rungs: list[LadderRung] = []
    for spec in cfg.fixed_ladder:
        base = materialize(spec, meta, "per_title")
        if base is None:
            continue
        bitrate = round_bitrate(base.bitrate_kbps * k, step)
        bitrate = min(max(bitrate, min_br), max_br)
        rungs.append(
            LadderRung(
                name=base.name,
                width=base.width,
                height=base.height,
                bitrate_kbps=bitrate,
                source="per_title",
            )
        )
    rungs = _ensure_increasing(rungs, step, max_br)
    if not rungs:
        raise ValueError("Per-title ladder rong.")
    return rungs


def _ensure_increasing(rungs: list[LadderRung], step: int, max_br: int) -> list[LadderRung]:
    if not rungs:
        return rungs
    out = [rungs[0]]
    for rung in rungs[1:]:
        prev = out[-1]
        bitrate = rung.bitrate_kbps
        if bitrate <= prev.bitrate_kbps:
            bitrate = min(max_br, prev.bitrate_kbps + step)
        out.append(
            LadderRung(
                name=rung.name,
                width=rung.width,
                height=rung.height,
                bitrate_kbps=bitrate,
                source=rung.source,
            )
        )
    return out


def validate_ladder(rungs: list[LadderRung], meta: VideoMeta, cfg: AppConfig) -> None:
    if not rungs:
        raise ValueError("Ladder rong.")
    min_br = int(cfg.complexity.get("min_bitrate_kbps", 150))
    max_br = int(cfg.complexity.get("max_bitrate_kbps", 8000))
    prev_br = 0
    for rung in rungs:
        if rung.width % 2 or rung.height % 2:
            raise ValueError(f"Kich thuoc le khong hop le yuv420p: {rung.width}x{rung.height}")
        if rung.width > meta.width or rung.height > meta.height:
            raise ValueError(f"Upscale bi cam: {rung.width}x{rung.height} > {meta.width}x{meta.height}")
        if rung.bitrate_kbps < min_br or rung.bitrate_kbps > max_br:
            raise ValueError(f"Bitrate ngoai bien: {rung.bitrate_kbps} kbps")
        if rung.bitrate_kbps <= prev_br:
            raise ValueError("Bitrate ladder phai tang dan.")
        prev_br = rung.bitrate_kbps


def build_candidate_rungs(meta: VideoMeta, cfg: AppConfig) -> list[LadderRung]:
    """Resolution x bitrate grid from YAML. Drops heights above the source."""
    if not cfg.candidates:
        raise ValueError("Thieu candidates trong config.")
    rungs: list[LadderRung] = []
    for spec in cfg.candidates:
        if spec.height > meta.height:
            continue
        if not spec.bitrates_kbps:
            raise ValueError(f"candidates height={spec.height} khong co bitrate.")
        width, height = size_for_height(meta, spec.height)
        seen: set[int] = set()
        for bitrate in spec.bitrates_kbps:
            if bitrate <= 0:
                raise ValueError(f"Bitrate candidate khong hop le: {bitrate}")
            if bitrate in seen:
                raise ValueError(f"Bitrate candidate trung: {bitrate} @ {spec.height}p")
            seen.add(bitrate)
            rungs.append(
                LadderRung(
                    name=f"{height}p_{bitrate}k",
                    width=width,
                    height=height,
                    bitrate_kbps=int(bitrate),
                    source="candidate",
                )
            )
    if not rungs:
        raise ValueError("Khong con candidate nao phu hop do phan giai nguon (khong upscale).")
    return rungs


def _ladder_bitrate(point: RQPoint) -> float:
    """Nominal ladder bitrate: target first, measured actual only as fallback."""
    if point.target_bitrate_kbps:
        return float(point.target_bitrate_kbps)
    return float(point.bitrate_kbps)


def select_ladder_from_hull(points: list[RQPoint], meta: VideoMeta, cfg: AppConfig) -> list[LadderRung]:
    """Hull-based Per-Title Ladder Selection (practical, not a global optimum).

    Efficient hull points are reduced to an ABR ladder with YAML constraints:
    min VMAF, one representative per height (highest VMAF, then lower bitrate),
    strictly increasing bitrate, then a cap on max_representations.
    """
    if not points:
        raise ValueError("Khong co diem hull de chon ladder.")
    sel = cfg.ladder_selection or {}
    max_reps = int(sel.get("max_representations", 4))
    min_vmaf = float(sel.get("min_vmaf", 0.0))
    one_per = bool(sel.get("prefer_one_per_height", True))
    filtered = [p for p in points if p.vmaf >= min_vmaf]
    if not filtered:
        filtered = list(points)
    if one_per:
        by_height: dict[int, list[RQPoint]] = {}
        for point in filtered:
            by_height.setdefault(int(point.height), []).append(point)
        chosen: list[RQPoint] = []
        for height in sorted(by_height):
            group = by_height[height]
            best = max(group, key=lambda item: (item.vmaf, -_ladder_bitrate(item)))
            chosen.append(best)
    else:
        chosen = sorted(filtered, key=_ladder_bitrate)
    chosen.sort(key=lambda item: (item.height, _ladder_bitrate(item)))
    monotonic: list[RQPoint] = []
    last_br = 0.0
    for point in chosen:
        bitrate = _ladder_bitrate(point)
        if bitrate > last_br:
            monotonic.append(point)
            last_br = bitrate
    if not monotonic:
        raise ValueError("Hull ladder rong sau rang buoc bitrate tang dan.")
    if max_reps < 1:
        raise ValueError("max_representations phai >= 1.")
    if len(monotonic) > max_reps:
        if max_reps == 1:
            monotonic = [monotonic[len(monotonic) // 2]]
        else:
            last = len(monotonic) - 1
            idxs = sorted({round(i * last / (max_reps - 1)) for i in range(max_reps)})
            monotonic = [monotonic[i] for i in idxs]
    rungs: list[LadderRung] = []
    for point in monotonic:
        width, height = size_for_height(meta, int(point.height) or 2)
        rungs.append(
            LadderRung(
                name=point.rung_name or f"{height}p",
                width=width,
                height=height,
                bitrate_kbps=int(point.target_bitrate_kbps or round(point.bitrate_kbps)),
                source="hull",
            )
        )
    return rungs
