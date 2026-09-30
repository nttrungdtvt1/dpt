"""Filesystem helpers. Never overwrite user source videos."""

from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def require_file(path: Path, what: str = "file") -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{what} khong ton tai: {path}")
    if not path.is_file():
        raise ValueError(f"{what} khong phai file: {path}")
    return path


def safe_stem(path: Path) -> str:
    stem = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in path.stem)
    return stem or "video"
