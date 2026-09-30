from dataclasses import replace
from types import SimpleNamespace

import pytest

from analysis.rq_points import RQPoint
from ladder.models import select_ladder_from_hull, validate_ladder


def _meta(width=1280, height=720):
    return SimpleNamespace(width=width, height=height, fps=25, duration_seconds=4)


def _pt(bitrate: float, vmaf: float, height: int, target: int | None = None) -> RQPoint:
    return RQPoint(
        bitrate_kbps=bitrate,
        vmaf=vmaf,
        height=height,
        target_bitrate_kbps=target if target is not None else int(bitrate),
        rung_name=f"{height}p_{int(target or bitrate)}k",
    )


def test_select_from_hull_points(test_cfg):
    hull = [
        _pt(280, 70, 360, 300),
        _pt(720, 85, 432, 730),
        _pt(1480, 93, 720, 1500),
    ]
    rungs = select_ladder_from_hull(hull, _meta(), test_cfg)
    assert [rung.height for rung in rungs] == [360, 432, 720]
    assert [rung.bitrate_kbps for rung in rungs] == [300, 730, 1500]
    assert all(rung.source == "hull" for rung in rungs)
    validate_ladder(rungs, _meta(), test_cfg)


def test_select_bitrate_monotonic(test_cfg):
    hull = [
        _pt(800, 88, 360, 700),
        _pt(500, 80, 432, 500),
        _pt(1500, 94, 720, 1500),
    ]
    rungs = select_ladder_from_hull(hull, _meta(), test_cfg)
    bitrates = [rung.bitrate_kbps for rung in rungs]
    assert bitrates == sorted(bitrates)
    assert len(set(bitrates)) == len(bitrates)


def test_select_max_representations(test_cfg):
    cfg = replace(test_cfg, ladder_selection={"max_representations": 2, "prefer_one_per_height": True, "min_vmaf": 0})
    hull = [
        _pt(300, 70, 360, 300),
        _pt(730, 85, 432, 730),
        _pt(1500, 93, 720, 1500),
        _pt(2800, 96, 720, 3000),
    ]
    rungs = select_ladder_from_hull(hull, _meta(), cfg)
    assert len(rungs) <= 2
    validate_ladder(rungs, _meta(), cfg)


def test_select_respects_source_resolution(test_cfg):
    hull = [_pt(300, 80, 360, 300), _pt(1500, 95, 720, 1500)]
    rungs = select_ladder_from_hull(hull, _meta(640, 360), test_cfg)
    assert all(rung.height <= 360 and rung.width <= 640 for rung in rungs)


def test_select_uses_target_bitrate_not_actual(test_cfg):
    """ABR monotonicity is on ladder targets; easy clips can share tiny actual bitrates."""
    hull = [
        RQPoint(bitrate_kbps=20, vmaf=99, height=360, target_bitrate_kbps=300, rung_name="360p_300k"),
        RQPoint(bitrate_kbps=21, vmaf=99, height=432, target_bitrate_kbps=730, rung_name="432p_730k"),
        RQPoint(bitrate_kbps=22, vmaf=99, height=720, target_bitrate_kbps=1500, rung_name="720p_1500k"),
    ]
    rungs = select_ladder_from_hull(hull, _meta(), test_cfg)
    assert [rung.bitrate_kbps for rung in rungs] == [300, 730, 1500]
    assert [rung.height for rung in rungs] == [360, 432, 720]


def test_select_empty_raises(test_cfg):
    with pytest.raises(ValueError, match="Khong co diem hull"):
        select_ladder_from_hull([], _meta(), test_cfg)
