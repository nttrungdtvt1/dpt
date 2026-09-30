from analysis.rq_points import RQPoint, pareto_frontier, remove_dominated_points


def _p(bitrate: float, vmaf: float, height: int = 360, name: str = "") -> RQPoint:
    return RQPoint(bitrate_kbps=bitrate, vmaf=vmaf, height=height, rung_name=name or f"{height}p_{int(bitrate)}")


def test_pareto_empty():
    assert pareto_frontier([]) == []
    assert remove_dominated_points([]) == []


def test_pareto_one_point():
    point = _p(500, 80)
    assert pareto_frontier([point]) == [point]


def test_pareto_duplicate_point():
    a = _p(500, 80, name="a")
    b = _p(500, 80, name="b")
    result = pareto_frontier([a, b])
    assert len(result) == 2
    assert {p.rung_name for p in result} == {"a", "b"}


def test_pareto_dominated_points():
    keep = _p(400, 90)
    dominated = _p(800, 70)
    also_dominated = _p(500, 80)
    result = pareto_frontier([dominated, keep, also_dominated])
    assert result == [keep]


def test_pareto_non_dominated_points():
    low = _p(300, 60)
    high = _p(900, 95)
    result = pareto_frontier([low, high])
    assert result == [low, high]


def test_pareto_equal_bitrate_keeps_higher_vmaf():
    worse = _p(500, 70)
    better = _p(500, 90)
    result = pareto_frontier([worse, better])
    assert result == [better]


def test_pareto_equal_vmaf_keeps_lower_bitrate():
    cheaper = _p(400, 80)
    costlier = _p(800, 80)
    result = pareto_frontier([costlier, cheaper])
    assert result == [cheaper]


def test_pareto_mixed_frontier():
    points = [
        _p(200, 40),
        _p(300, 70),
        _p(350, 65),  # dominated by 300@70
        _p(600, 88),
        _p(900, 90),
    ]
    result = pareto_frontier(points)
    assert [p.bitrate_kbps for p in result] == [200, 300, 600, 900]
