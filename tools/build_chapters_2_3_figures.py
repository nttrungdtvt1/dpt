"""Illustrative figures for Chapters 2–3 (not experimental results)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, FancyArrow

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "chapter23_figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.unicode_minus": False,
        "figure.dpi": 140,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    }
)


def fig_rq_curve() -> Path:
    """Hypothetical bitrate–VMAF curve with diminishing returns."""
    br = [250, 365, 500, 700, 1000, 1500, 2000, 3000]
    vmaf = [68.0, 74.5, 80.0, 85.0, 89.0, 92.2, 93.6, 94.4]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(br, vmaf, "-o", color="#1F4E79", lw=2, ms=7, label="Vi du duong cong (minh hoa)")
    ax.annotate(
        "Loi ich bien giam dan",
        xy=(2500, 94.0),
        xytext=(1700, 78),
        arrowprops=dict(arrowstyle="->", color="#C0392B"),
        color="#C0392B",
        fontsize=9,
    )
    ax.set_xlabel("Bitrate thuc te (kbps)")
    ax.set_ylabel("VMAF")
    ax.set_title("Vi du minh hoa duong cong bitrate–quality (khong phai so lieu de tai)")
    ax.grid(True, alpha=0.35)
    ax.set_ylim(60, 100)
    ax.legend(loc="lower right")
    path = OUT / "fig_2_1_bitrate_quality.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_pareto() -> Path:
    bitrates = [300, 500, 700, 900, 1200, 1500, 1800]
    vmafs = [72, 78, 77, 86, 88, 87, 93]
    dominated_idx = {2, 5}  # 700@77 dominated by 500@78; 1500@87 by 1200@88
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for i, (x, y) in enumerate(zip(bitrates, vmafs)):
        if i in dominated_idx:
            ax.scatter(x, y, s=70, c="#C0392B", marker="x", zorder=3, label="Bi chi phoi" if i == 2 else None)
        else:
            ax.scatter(x, y, s=55, c="#1F4E79", zorder=3, label="Pareto" if i == 0 else None)
    px = [bitrates[i] for i in range(len(bitrates)) if i not in dominated_idx]
    py = [vmafs[i] for i in range(len(vmafs)) if i not in dominated_idx]
    ax.plot(px, py, "--", color="#1F4E79", alpha=0.7)
    ax.annotate("B tot hon A\n(bitrate thap hon, VMAF cao hon)", xy=(500, 78), xytext=(750, 70),
                arrowprops=dict(arrowstyle="->", color="#7D3C98"), fontsize=8, color="#7D3C98")
    ax.set_xlabel("Bitrate (kbps)")
    ax.set_ylabel("VMAF")
    ax.set_title("Vi du minh hoa Pareto dominance (khong phai so lieu de tai)")
    ax.grid(True, alpha=0.35)
    ax.legend()
    path = OUT / "fig_2_2_pareto.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_hull() -> Path:
    # Pareto points; one concave dip so hull skips an interior Pareto point
    px = [250, 400, 800, 1400, 2200]
    py = [70.0, 82.0, 86.0, 93.0, 95.5]
    # hull skips (800, 86)
    hx = [250, 400, 1400, 2200]
    hy = [70.0, 82.0, 93.0, 95.5]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(px, py, "o--", color="#5B2C6F", lw=1.4, label="Pareto frontier")
    ax.plot(hx, hy, "-s", color="#117A65", lw=2.2, ms=7, label="Upper convex envelope")
    ax.scatter([800], [86], s=80, facecolors="none", edgecolors="#C0392B", lw=1.6, zorder=4)
    ax.annotate("Diem Pareto khong nam tren bao loi", xy=(800, 86), xytext=(950, 76),
                arrowprops=dict(arrowstyle="->", color="#C0392B"), fontsize=8, color="#C0392B")
    ax.set_xlabel("Bitrate (kbps)")
    ax.set_ylabel("VMAF")
    ax.set_title("Pareto frontier khac upper convex envelope (minh hoa)")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="lower right")
    path = OUT / "fig_2_3_convex_hull.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def _box(ax, x, y, w, h, text, color, kind="round"):
    if kind == "diamond":
        pts = [(x, y + h / 2), (x + w / 2, y + h), (x + w, y + h / 2), (x + w / 2, y)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor="#1C2833", lw=1.1))
    else:
        rad = 0.35 if kind == "terminator" else 0.12
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle=f"round,pad=0.02,rounding_size={rad}",
                facecolor=color,
                edgecolor="#1C2833",
                lw=1.1,
            )
        )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.2, color="#1C2833")


def _arrow(ax, x1, y1, x2, y2):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=9,
            lw=1.05,
            color="#1C2833",
        )
    )


def fig_flowchart() -> Path:
    fig, ax = plt.subplots(figsize=(8.6, 11.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 16.2)
    ax.axis("off")
    ax.set_title("Quy trinh nghien cuu (phuong phap de tai)", fontsize=11, pad=8)

    C_P, C_D, C_E, C_I = "#D6EAF8", "#FCF3CF", "#D5F5E3", "#D7BDE2"
    items = [
        (7, 15.4, 2.2, 0.55, "Bat dau", C_E, "terminator"),
        (6.6, 14.55, 3.0, 0.6, "Nhap video + cau hinh", C_I, "round"),
        (6.6, 13.7, 3.0, 0.6, "Chuan hoa / FFprobe", C_P, "round"),
        (6.4, 12.85, 3.4, 0.6, "Phan tich SI/TI (mo ta)", C_P, "round"),
        (6.4, 12.0, 3.4, 0.6, "Tao luoi candidate", C_P, "round"),
        (6.4, 11.15, 3.4, 0.6, "Encode candidate (FFmpeg)", C_P, "round"),
        (6.15, 10.25, 3.9, 0.65, "Do bitrate thuc, dung luong, VMAF", C_P, "round"),
        (6.6, 9.4, 3.0, 0.55, "Luu du lieu candidate", C_I, "round"),
        (6.3, 8.55, 3.6, 0.6, "Duong cong bitrate–VMAF", C_P, "round"),
        (6.5, 7.7, 3.2, 0.55, "Loc Pareto", C_P, "round"),
        (6.2, 6.85, 3.8, 0.6, "Upper convex envelope", C_P, "round"),
        (6.15, 5.95, 3.9, 0.7, "Chon ladder theo quy tac de xuat", C_D, "round"),
        (6.3, 5.05, 3.6, 0.6, "Xay dung / doc baseline co dinh", C_P, "round"),
        (6.5, 4.2, 3.2, 0.55, "So sanh KPI", C_P, "round"),
        (6.3, 3.35, 3.6, 0.6, "Xuat bang, bieu do, ket qua", C_I, "round"),
        (7, 2.45, 2.2, 0.55, "Ket thuc", C_E, "terminator"),
    ]
    # left note
    _box(ax, 0.35, 12.7, 4.3, 1.35, "SI/TI khong chon ladder chinh\nchi mo ta noi dung\nva heuristic k x fixed", "#FADBD8", "round")
    _box(ax, 0.35, 6.4, 4.3, 1.5, "Pareto loc candidate kem hieu qua\nHull ho tro phan tich envelope\nChon ladder la buoc rieng", "#FDEBD0", "round")
    _box(ax, 0.35, 3.9, 4.3, 1.2, "Baseline: ladder co dinh\n(cung codec, cung dieu kien do)", "#D5F5E3", "round")

    for x, y, w, h, text, color, kind in items:
        _box(ax, x, y, w, h, text, color, kind)

    ys = [15.4, 14.55, 13.7, 12.85, 12.0, 11.15, 10.25, 9.4, 8.55, 7.7, 6.85, 5.95, 5.05, 4.2, 3.35, 2.45]
    hs = [0.55, 0.6, 0.6, 0.6, 0.6, 0.6, 0.65, 0.55, 0.6, 0.55, 0.6, 0.7, 0.6, 0.55, 0.6, 0.55]
    cx = 8.1
    for i in range(len(ys) - 1):
        y_from = ys[i]
        y_to = ys[i + 1] + hs[i + 1]
        _arrow(ax, cx, y_from, cx, y_to + 0.02)

    path = OUT / "fig_3_1_flowchart.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_io() -> Path:
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    _box(ax, 0.3, 1.1, 2.4, 1.1, "Dau vao\nvideo, YAML\nluoi candidate", "#D7BDE2")
    _box(ax, 3.5, 0.85, 3.0, 1.6, "Xu ly\nencode, VMAF,\nPareto, hull,\nchon ladder", "#D6EAF8")
    _box(ax, 7.3, 1.1, 2.4, 1.1, "Dau ra\nladder de xuat\nKPI, bieu do", "#D5F5E3")
    _arrow(ax, 2.75, 1.65, 3.45, 1.65)
    _arrow(ax, 6.55, 1.65, 7.25, 1.65)
    ax.set_title("Mo hinh dau vao – xu ly – dau ra", fontsize=11)
    path = OUT / "fig_3_0_io.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> None:
    paths = [fig_rq_curve(), fig_pareto(), fig_hull(), fig_io(), fig_flowchart()]
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
