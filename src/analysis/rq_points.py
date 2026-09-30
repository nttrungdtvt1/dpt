"""Rate-quality points: Pareto frontier and upper convex hull.

These two sets are not the same:

    Candidate points
          ↓
    Remove dominated points
          ↓
    Pareto frontier          (non-dominated encodings)
          ↓
    Upper convex hull        (convex envelope of Pareto in bitrate–VMAF)

Objective: minimize bitrate, maximize VMAF.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RQPoint:
    """One measured encoding: actual bitrate vs VMAF (plus ladder metadata)."""

    bitrate_kbps: float
    vmaf: float
    width: int = 0
    height: int = 0
    target_bitrate_kbps: int = 0
    rung_name: str = ""
    size_bytes: int = 0
    encode_seconds: float = 0.0
    psnr: float | None = None
    ssim: float | None = None
    output_file: str = ""


def _finite(point: RQPoint) -> bool:
    return math.isfinite(point.bitrate_kbps) and math.isfinite(point.vmaf)


def remove_dominated_points(points: Sequence[RQPoint]) -> list[RQPoint]:
    """Keep points that are not dominated under min-bitrate, max-VMAF.

    B dominates A if B.bitrate <= A.bitrate and B.vmaf >= A.vmaf
    and at least one inequality is strict.
    """
    valid = [p for p in points if p is not None and _finite(p)]
    kept: list[RQPoint] = []
    for a in valid:
        dominated = False
        for b in valid:
            if a is b:
                continue
            bitrate_le = b.bitrate_kbps <= a.bitrate_kbps
            vmaf_ge = b.vmaf >= a.vmaf
            strict = (b.bitrate_kbps < a.bitrate_kbps) or (b.vmaf > a.vmaf)
            if bitrate_le and vmaf_ge and strict:
                dominated = True
                break
        if not dominated:
            kept.append(a)
    kept.sort(key=lambda p: (p.bitrate_kbps, -p.vmaf, p.height))
    return kept


def pareto_frontier(points: Sequence[RQPoint]) -> list[RQPoint]:
    """Non-dominated set. Not the same as a convex hull."""
    return remove_dominated_points(points)


def _cross(o: RQPoint, a: RQPoint, b: RQPoint) -> float:
    return (a.bitrate_kbps - o.bitrate_kbps) * (b.vmaf - o.vmaf) - (a.vmaf - o.vmaf) * (
        b.bitrate_kbps - o.bitrate_kbps
    )


def upper_convex_hull(points: Sequence[RQPoint]) -> list[RQPoint]:
    """Upper convex hull of (bitrate, VMAF) via monotone chain.

    Walk left-to-right and keep only clockwise turns so the chain is the
    upper envelope (max VMAF). Collinear interior points are dropped
    (`cross >= 0` pops). Duplicate bitrates keep the highest VMAF.

    Call this on the Pareto frontier in the scientific pipeline; the
    geometry still holds if dominated points are left in.
    """
    valid = [p for p in points if p is not None and _finite(p)]
    if not valid:
        return []
    best: dict[float, RQPoint] = {}
    for point in valid:
        prev = best.get(point.bitrate_kbps)
        if prev is None or point.vmaf > prev.vmaf:
            best[point.bitrate_kbps] = point
    unique = sorted(best.values(), key=lambda p: (p.bitrate_kbps, p.vmaf))
    if len(unique) <= 2:
        return unique

    hull: list[RQPoint] = []
    for point in unique:
        while len(hull) >= 2 and _cross(hull[-2], hull[-1], point) >= 0:
            hull.pop()
        hull.append(point)
    return hull
