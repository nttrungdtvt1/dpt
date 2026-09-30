"""Create small synthetic clips for tests and first-run demos."""

from __future__ import annotations

from pathlib import Path

from utils.ffmpeg_tools import FFmpegTools, require_success, run_ffmpeg


def make_sample_video(
    tools: FFmpegTools,
    output: Path,
    seconds: float = 2.0,
    size: str = "640x360",
    rate: int = 25,
    pattern: str = "testsrc",
) -> Path:
    """Generate a short H.264 clip. `pattern` is an FFmpeg lavfi source name."""
    output.parent.mkdir(parents=True, exist_ok=True)
    source = f"{pattern}=size={size}:rate={rate}:duration={seconds}"
    args = [
        str(tools.ffmpeg),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        source,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "ultrafast",
        str(output),
    ]
    completed = run_ffmpeg(args, timeout=60)
    require_success(completed, f"tao sample {output.name}")
    if not output.is_file():
        raise RuntimeError(f"Khong tao duoc video mau: {output}")
    return output
