from __future__ import annotations

from pathlib import Path

import pytest

from config import load_config
from utils.ffmpeg_tools import FFmpegNotFoundError, find_ffmpeg_tools
from utils.sample_video import make_sample_video

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def ffmpeg_tools():
    try:
        return find_ffmpeg_tools()
    except FFmpegNotFoundError as exc:
        pytest.skip(str(exc))


@pytest.fixture
def test_cfg():
    return load_config(ROOT / "tests" / "test_config.yaml")


@pytest.fixture
def sample_video(tmp_path, ffmpeg_tools):
    path = tmp_path / "sample.mp4"
    return make_sample_video(
        ffmpeg_tools,
        path,
        seconds=1.2,
        size="640x360",
        rate=25,
        pattern="testsrc",
    )
