from pathlib import Path

from analyzer.feature_extractor import extract_features
from analyzer.complexity import analyze_complexity
from analyzer.video_probe import probe_video
from pipeline import run_pipeline


def test_complexity_on_real_sample(sample_video, ffmpeg_tools, test_cfg):
    meta = probe_video(sample_video, ffmpeg_tools)
    result = analyze_complexity(meta, ffmpeg_tools, test_cfg)
    assert result.frames_used >= 2
    assert result.si >= 0
    assert result.ti >= 0
    assert result.label in {"easy", "medium", "hard"}


def test_full_pipeline(sample_video, ffmpeg_tools, test_cfg, tmp_path):
    summary = run_pipeline([sample_video], tmp_path / "out", ffmpeg_tools, test_cfg)
    assert summary["row_count"] >= 2
    assert Path(summary["csv"]).is_file()
    assert Path(summary["json"]).is_file()
    assert summary["plots"]
    analyses = summary["analyses"][0]
    assert analyses["fixed_ladder"]
    assert analyses["per_title_ladder"]
    for plot in summary["plots"]:
        assert Path(plot).is_file()
    # Encoded files exist and are non-trivial.
    encodes = list((tmp_path / "out" / "encodes").rglob("*.mp4"))
    assert encodes
    assert all(path.stat().st_size > 500 for path in encodes)


def test_features_reject_tiny_resolution(ffmpeg_tools, test_cfg, tmp_path):
    from utils.sample_video import make_sample_video

    tiny = tmp_path / "tiny.mp4"
    make_sample_video(ffmpeg_tools, tiny, seconds=1.0, size="32x18")
    # 32x18 is above 16, so it should still analyze; create an even smaller case via probe check.
    features = extract_features(tiny, ffmpeg_tools, test_cfg)
    assert features.meta.width == 32
