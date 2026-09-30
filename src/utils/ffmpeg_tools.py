"""Locate and invoke FFmpeg/FFprobe without using a shell."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class FFmpegNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class FFmpegTools:
    ffmpeg: Path
    ffprobe: Path


def _candidate_bins() -> list[Path]:
    found: list[Path] = []
    which = shutil.which("ffmpeg")
    if which:
        found.append(Path(which))
    env = os.environ.get("FFMPEG_BIN") or os.environ.get("FFMPEG_PATH")
    if env:
        found.append(Path(env))
    local = os.environ.get("LOCALAPPDATA")
    if local:
        winget = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if winget.exists():
            found.extend(winget.glob("Gyan.FFmpeg*/**/bin/ffmpeg.exe"))
    return found


def find_ffmpeg_tools() -> FFmpegTools:
    for ffmpeg in _candidate_bins():
        if ffmpeg.is_file():
            probe = ffmpeg.with_name("ffprobe.exe" if ffmpeg.suffix.lower() == ".exe" else "ffprobe")
            if probe.is_file():
                return FFmpegTools(ffmpeg=ffmpeg, ffprobe=probe)
    raise FFmpegNotFoundError(
        "Khong tim thay FFmpeg/FFprobe. Cai dat FFmpeg va dam bao ffmpeg nam trong PATH, "
        "hoac dat bien FFMPEG_BIN tro toi ffmpeg.exe."
    )


def run_ffmpeg(args: list[str], timeout: int | None = 600) -> subprocess.CompletedProcess[str]:
    if not args:
        raise ValueError("Danh sach tham so FFmpeg rong.")
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False,
    )
    return completed


def require_success(completed: subprocess.CompletedProcess[str], context: str) -> None:
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "")[-2000:]
        raise RuntimeError(f"{context} that bai (exit {completed.returncode}).\n{tail}")
