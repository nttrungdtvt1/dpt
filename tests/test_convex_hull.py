import math

from analysis.rq_points import RQPoint, pareto_frontier, upper_convex_hull


def _p(bitrate: float, vmaf: float, height: int = 360) -> RQPoint:
    return RQPoint(bitrate_kbps=bitrate, vmaf=vmaf, height=height, target_bitrate_kbps=int(bitrate))


def test_hull_empty():
    assert upper_convex_hull([]) == []


def test_hull_one_point():
    point = _p(100, 50)
    assert upper_convex_hull([point]) == [point]


def test_hull_two_points():
    a, b = _p(100, 50), _p(400, 90)
    assert upper_convex_hull([a, b]) == [a, b]


def test_hull_collinear_drops_middle():
    points = [_p(100, 10), _p(200, 20), _p(300, 30)]
    hull = upper_convex_hull(points)
    assert [p.bitrate_kbps for p in hull] == [100, 300]


def test_hull_duplicate_bitrate_keeps_higher_vmaf():
    hull = upper_convex_hull([_p(200, 40), _p(200, 70), _p(400, 90)])
    assert [p.bitrate_kbps for p in hull] == [200, 400]
    assert hull[0].vmaf == 70


def test_hull_upper_envelope_drops_concave_point():
    # (3, 3.5) sits below the chord (2,3)-(4,6).
    points = [_p(1, 1), _p(2, 3), _p(3, 3.5), _p(4, 6)]
    hull = upper_convex_hull(points)
    assert [(p.bitrate_kbps, p.vmaf) for p in hull] == [(1, 1), (2, 3), (4, 6)]


def test_hull_after_dominated_removed():
    raw = [_p(100, 90), _p(200, 40), _p(300, 95)]
    pareto = pareto_frontier(raw)
    hull = upper_convex_hull(pareto)
    assert [p.bitrate_kbps for p in pareto] == [100, 300]
    assert [p.bitrate_kbps for p in hull] == [100, 300]
    # Geometry also drops the interior dominated point if called directly.
    assert [p.bitrate_kbps for p in upper_convex_hull(raw)] == [100, 300]


def test_hull_ignores_non_finite():
    bad = RQPoint(bitrate_kbps=math.nan, vmaf=50.0)
    inf = RQPoint(bitrate_kbps=100.0, vmaf=math.inf)
    good = _p(150, 70)
    assert upper_convex_hull([bad, inf, good]) == [good]
