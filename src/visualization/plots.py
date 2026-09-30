"""Matplotlib charts for the comparison report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from metrics.result_collector import ExperimentRow

import matplotlib

matplotlib.use("Agg")

_LADDER_METHODS = ("fixed", "per_title", "hull")
_METHOD_COLORS = {
    "fixed": "#4C78A8",
    "per_title": "#F58518",
    "hull": "#54A24B",
    "candidate": "#B279A2",
}
_METHOD_LABELS = {
    "fixed": "fixed",
    "per_title": "heuristic (k x fixed)",
    "hull": "hull-based",
    "candidate": "candidate",
}


def plot_results(
    rows: list[ExperimentRow],
    out_dir: Path,
    analyses: list[dict[str, Any]] | None = None,
) -> list[Path]:
    if not rows:
        raise ValueError("Khong co du lieu de ve bieu do.")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    videos = sorted({row.video for row in rows})
    methods = sorted({row.method for row in rows})
    ladder_rows = [row for row in rows if row.method in _LADDER_METHODS]
    size_rows = ladder_rows or rows

    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels = [f"{row.video}\n{row.method}\n{row.rung}" for row in size_rows]
    sizes_mb = [row.size_bytes / (1024 * 1024) for row in size_rows]
    colors = [_METHOD_COLORS.get(row.method, "#9E9E9E") for row in size_rows]
    ax.bar(range(len(size_rows)), sizes_mb, color=colors)
    ax.set_xticks(range(len(size_rows)), labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Dung luong (MB)")
    ax.set_title("Dung luong file theo bac va phuong phap")
    fig.tight_layout()
    path = out_dir / "file_size_by_rung.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    created.append(path)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for method in methods:
        subset = [row for row in rows if row.method == method and row.ssim is not None]
        subset.sort(key=lambda item: item.actual_bitrate_kbps)
        if not subset:
            continue
        ax.plot(
            [row.actual_bitrate_kbps for row in subset],
            [row.ssim for row in subset],
            marker="o",
            color=_METHOD_COLORS.get(method),
            label=_METHOD_LABELS.get(method, method),
        )
    ax.set_xlabel("Bitrate thuc te (kbps)")
    ax.set_ylabel("SSIM (scale ve do phan giai nguon)")
    ax.set_title("Duong bitrate-SSIM")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = out_dir / "bitrate_ssim.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    created.append(path)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bar_labels: list[str] = []
    bar_values: list[float] = []
    bar_colors: list[str] = []
    for video in videos:
        subset = [row for row in rows if row.video == video]
        present = {row.method for row in subset}
        for method in _LADDER_METHODS:
            if method not in present and method == "hull":
                continue
            if method not in present and method not in {"fixed", "per_title"}:
                continue
            total = sum(row.size_bytes for row in subset if row.method == method)
            bar_labels.append(f"{video}\n{_METHOD_LABELS.get(method, method)}")
            bar_values.append(total / 1024)
            bar_colors.append(_METHOD_COLORS.get(method, "#9E9E9E"))
    ax.bar(bar_labels, bar_values, color=bar_colors)
    ax.set_ylabel("Tong dung luong ladder (KB)")
    ax.set_title("Tong dung luong toan ladder")
    fig.tight_layout()
    path = out_dir / "ladder_total_size.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    created.append(path)

    vmaf_path = _plot_bitrate_vmaf(rows, out_dir, analyses)
    if vmaf_path is not None:
        created.append(vmaf_path)
    return created


def _plot_bitrate_vmaf(
    rows: list[ExperimentRow],
    out_dir: Path,
    analyses: list[dict[str, Any]] | None,
) -> Path | None:
    import matplotlib.pyplot as plt

    videos = sorted({row.video for row in rows})
    has_vmaf = any(row.vmaf is not None for row in rows)
    if not has_vmaf and not analyses:
        return None

    n = max(len(videos), 1)
    fig, axes = plt.subplots(n, 1, figsize=(8, 4.2 * n), squeeze=False)
    for idx, video in enumerate(videos):
        ax = axes[idx][0]
        analysis = None
        if analyses:
            analysis = next((item for item in analyses if item.get("video") == video), None)

        candidate_rows = [row for row in rows if row.video == video and row.method == "candidate" and row.vmaf is not None]
        if not candidate_rows:
            candidate_rows = [row for row in rows if row.video == video and row.vmaf is not None]
        ax.scatter(
            [row.actual_bitrate_kbps for row in candidate_rows],
            [row.vmaf for row in candidate_rows],
            c="#B279A2",
            s=36,
            zorder=3,
            label="Candidate",
        )

        pareto = (analysis or {}).get("pareto") or []
        if pareto:
            ordered = sorted(pareto, key=lambda item: item["bitrate_kbps"])
            ax.scatter(
                [item["bitrate_kbps"] for item in ordered],
                [item["vmaf"] for item in ordered],
                facecolors="none",
                edgecolors="#4C78A8",
                s=80,
                linewidths=1.4,
                zorder=4,
                label="Pareto frontier",
            )

        hull = (analysis or {}).get("convex_hull") or []
        if hull:
            ordered = sorted(hull, key=lambda item: item["bitrate_kbps"])
            ax.plot(
                [item["bitrate_kbps"] for item in ordered],
                [item["vmaf"] for item in ordered],
                color="#54A24B",
                linewidth=2,
                marker="s",
                zorder=5,
                label="Upper convex hull",
            )

        selected = [
            row
            for row in rows
            if row.video == video and row.method == "hull" and row.vmaf is not None
        ]
        if selected:
            ax.scatter(
                [row.actual_bitrate_kbps for row in selected],
                [row.vmaf for row in selected],
                c="#E45756",
                marker="*",
                s=160,
                zorder=6,
                label="Selected hull ladder",
            )

        ax.set_xlabel("Bitrate thuc te (kbps)")
        ax.set_ylabel("VMAF")
        ax.set_title(f"Bitrate-VMAF: {video}")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    path = out_dir / "bitrate_vmaf.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
