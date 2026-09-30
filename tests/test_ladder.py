from types import SimpleNamespace

import pytest

from ladder.models import (
    LadderRung,
    build_fixed_ladder,
    build_per_title_ladder,
    size_for_height,
    validate_ladder,
)


def _meta(width=1920, height=1080):
    return SimpleNamespace(width=width, height=height, fps=25, duration_seconds=10)


def test_no_upscale_1080_source(test_cfg):
    meta = _meta(1920, 1080)
    rungs = build_fixed_ladder(meta, test_cfg)
    assert rungs
    assert all(r.height <= 1080 and r.width <= 1920 for r in rungs)


def test_720_source_drops_taller_rungs(test_cfg):
    meta = _meta(1280, 720)
    rungs = build_fixed_ladder(meta, test_cfg)
    assert all(r.height <= 720 for r in rungs)


def test_360_source_keeps_only_360_or_less(test_cfg):
    meta = _meta(640, 360)
    rungs = build_fixed_ladder(meta, test_cfg)
    assert rungs
    assert all(r.height <= 360 for r in rungs)


def test_even_dimensions():
    meta = _meta(1279, 719)
    width, height = size_for_height(meta, 360)
    assert width % 2 == 0
    assert height % 2 == 0


def test_per_title_scales_bitrate(test_cfg):
    meta = _meta()
    fixed = build_fixed_ladder(meta, test_cfg)
    easy = build_per_title_ladder(meta, test_cfg, k=0.65)
    hard = build_per_title_ladder(meta, test_cfg, k=1.35)
    assert easy[0].bitrate_kbps < fixed[0].bitrate_kbps
    assert hard[0].bitrate_kbps > fixed[0].bitrate_kbps


def test_validate_rejects_upscale(test_cfg):
    meta = _meta(640, 360)
    bad = [LadderRung("1080p", 1920, 1080, 6000, "fixed")]
    with pytest.raises(ValueError, match="Upscale"):
        validate_ladder(bad, meta, test_cfg)


def test_validate_rejects_non_increasing(test_cfg):
    meta = _meta()
    bad = [
        LadderRung("a", 640, 360, 800, "fixed"),
        LadderRung("b", 768, 432, 700, "fixed"),
    ]
    with pytest.raises(ValueError, match="tang dan"):
        validate_ladder(bad, meta, test_cfg)


def test_validate_bitrate_bounds(test_cfg):
    meta = _meta()
    bad = [LadderRung("a", 640, 360, 10, "fixed")]
    with pytest.raises(ValueError, match="ngoai bien"):
        validate_ladder(bad, meta, test_cfg)
