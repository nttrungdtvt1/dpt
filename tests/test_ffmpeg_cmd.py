from encoder.ffmpeg_encoder import _base_args
from analyzer.video_probe import probe_video
from ladder.models import build_fixed_ladder


def test_ffmpeg_args_are_list_and_keep_spaces(sample_video, ffmpeg_tools, test_cfg, tmp_path):
    spaced = tmp_path / "video with spaces.mp4"
    spaced.write_bytes(sample_video.read_bytes())
    meta = probe_video(spaced, ffmpeg_tools)
    rungs = build_fixed_ladder(meta, test_cfg)
    args = _base_args(ffmpeg_tools, spaced, rungs[0], test_cfg, meta)
    assert args[0] == str(ffmpeg_tools.ffmpeg)
    assert str(spaced) in args
    assert all(isinstance(item, str) for item in args)
    joined = " ".join(args)
    assert "-b:v" in args
    assert "-vf" in args
    assert "scale=" in joined
