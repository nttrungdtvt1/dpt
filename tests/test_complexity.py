import numpy as np

from analyzer.complexity import (
    classify_complexity,
    complexity_index,
    spatial_information,
    temporal_information,
)


def test_flat_frame_has_low_si():
    frame = np.full((64, 64), 128, dtype=np.uint8)
    assert spatial_information(frame) < 1.0


def test_edge_frame_has_higher_si_than_flat():
    flat = np.full((64, 64), 128, dtype=np.uint8)
    edge = np.zeros((64, 64), dtype=np.uint8)
    edge[:, 32:] = 255
    assert spatial_information(edge) > spatial_information(flat) + 20


def test_shifted_frame_has_higher_ti():
    a = np.zeros((48, 48), dtype=np.uint8)
    b = np.zeros((48, 48), dtype=np.uint8)
    a[:, :24] = 255
    b[:, 12:36] = 255
    assert temporal_information(a, a) == 0.0
    assert temporal_information(a, b) > 10


def test_classify_thresholds(test_cfg):
    label, k = classify_complexity(0.1, test_cfg)
    assert label == "easy"
    assert k == test_cfg.complexity["k_easy"]
    label, k = classify_complexity(0.5, test_cfg)
    assert label == "medium"
    label, k = classify_complexity(0.9, test_cfg)
    assert label == "hard"


def test_index_increases_with_si_ti(test_cfg):
    low = complexity_index(5, 2, test_cfg)
    high = complexity_index(80, 40, test_cfg)
    assert high > low
