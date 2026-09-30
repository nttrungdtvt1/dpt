from pathlib import Path

from utils.ffmpeg_tools import find_ffmpeg_tools


def test_find_ffmpeg(ffmpeg_tools):
    tools = find_ffmpeg_tools()
    assert tools.ffmpeg.is_file()
    assert tools.ffprobe.is_file()
    assert tools.ffmpeg.name.lower().startswith("ffmpeg")
