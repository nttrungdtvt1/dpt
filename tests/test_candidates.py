from dataclasses import replace
from types import SimpleNamespace

import pytest

from config import CandidateSpec
from ladder.models import build_candidate_rungs


def _meta(width=1280, height=720):
    return SimpleNamespace(width=width, height=height, fps=25, duration_seconds=4)


def test_candidates_from_valid_config(test_cfg):
    rungs = build_candidate_rungs(_meta(), test_cfg)
    heights = {rung.height for rung in rungs}
    assert 360 in heights
    assert 720 in heights
    bitrates_360 = [rung.bitrate_kbps for rung in rungs if rung.height == 360]
    assert bitrates_360 == [300, 500]
    assert all(rung.source == "candidate" for rung in rungs)


def test_candidates_no_upscale(test_cfg):
    rungs = build_candidate_rungs(_meta(640, 360), test_cfg)
    assert rungs
    assert all(rung.height <= 360 and rung.width <= 640 for rung in rungs)
    assert all(rung.height != 720 for rung in rungs)


def test_candidates_multiple_bitrate_per_height(test_cfg):
    rungs = build_candidate_rungs(_meta(), test_cfg)
    by_height = {}
    for rung in rungs:
        by_height.setdefault(rung.height, []).append(rung.bitrate_kbps)
    assert all(len(values) >= 2 for values in by_height.values())


def test_candidates_invalid_bitrate(test_cfg):
    cfg = replace(test_cfg, candidates=(CandidateSpec(height=360, bitrates_kbps=(0, 300)),))
    with pytest.raises(ValueError, match="khong hop le"):
        build_candidate_rungs(_meta(), cfg)


def test_candidates_duplicate_bitrate(test_cfg):
    cfg = replace(test_cfg, candidates=(CandidateSpec(height=360, bitrates_kbps=(300, 300)),))
    with pytest.raises(ValueError, match="trung"):
        build_candidate_rungs(_meta(), cfg)


def test_candidates_empty_grid(test_cfg):
    cfg = replace(test_cfg, candidates=())
    with pytest.raises(ValueError, match="Thieu candidates"):
        build_candidate_rungs(_meta(), cfg)
