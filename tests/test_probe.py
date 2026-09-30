from pathlib import Path

import pytest

from analyzer.video_probe import probe_video
from utils.filesystem import require_file


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        require_file(Path("khong_ton_tai_abc.mp4"), "video")


def test_probe_rejects_non_video(tmp_path, ffmpeg_tools):
    junk = tmp_path / "not_video.txt"
    junk.write_text("hello", encoding="utf-8")
    with pytest.raises(Exception):
        probe_video(junk, ffmpeg_tools)


def test_probe_reads_metadata(sample_video, ffmpeg_tools):
    meta = probe_video(sample_video, ffmpeg_tools)
    assert meta.width == 640
    assert meta.height == 360
    assert meta.fps > 0
    assert meta.duration_seconds > 0.5
    assert meta.codec in {"h264", "avc1", "libx264"} or meta.codec
