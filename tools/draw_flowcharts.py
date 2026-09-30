"""Flowcharts drawn from the real call graph — branches and loops are explicit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "flowcharts"

C_PROC = "#D6EAF8"
C_DEC = "#FCF3CF"
C_END = "#D5F5E3"
C_ERR = "#F5B7B1"
C_IO = "#D7BDE2"
C_LOOP = "#FAD7A0"
EDGE = "#1C2833"


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    kind: str = "round"

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def top(self) -> float:
        return self.y + self.h

    @property
    def bot(self) -> float:
        return self.y

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.w


class Canvas:
    def __init__(self, width: float, height: float, title: str):
        self.fig, self.ax = plt.subplots(figsize=(width, height))
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, height)
        self.ax.axis("off")
        self.ax.set_title(title, fontsize=8.5, color="#7B241C", pad=6)
        self.H = height

    def box(self, x, y, w, h, text, color, kind="round", size=7.0) -> Box:
        node = Box(x, y, w, h, kind)
        if kind == "diamond":
            pts = [
                (x, y + h / 2),
                (x + w / 2, y + h),
                (x + w, y + h / 2),
                (x + w / 2, y),
            ]
            self.ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor=EDGE, lw=1.15))
        else:
            rad = 0.28 if kind == "terminator" else 0.10
            self.ax.add_patch(
                FancyBboxPatch(
                    (x, y),
                    w,
                    h,
                    boxstyle=f"round,pad=0.015,rounding_size={rad}",
                    facecolor=color,
                    edgecolor=EDGE,
                    lw=1.15,
                )
            )
        self.ax.text(node.cx, node.cy, text, ha="center", va="center", fontsize=size, color="#1B2631")
        return node

    def arrow(self, x1, y1, x2, y2, label="", side="right"):
        self.ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=9,
                lw=1.05,
                color=EDGE,
                connectionstyle="arc3,rad=0",
            )
        )
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx = 0.16 if side == "right" else -0.16
            if side == "above":
                my += 0.12
                dx = 0
            elif side == "below":
                my -= 0.14
                dx = 0
            self.ax.text(mx + dx, my, label, fontsize=6.4, color="#922B21", ha="center", va="center", fontweight="bold")

    def down(self, a: Box, b: Box, label="", side="right"):
        self.arrow(a.cx, a.bot, b.cx, b.top, label, side)

    def right(self, a: Box, b: Box, label=""):
        self.arrow(a.right, a.cy, b.left, b.cy, label, "above")

    def left(self, a: Box, b: Box, label=""):
        self.arrow(a.left, a.cy, b.right, b.cy, label, "above")

    def loop_left(self, src: Box, dst: Box, label="YES", inset: float = 0.42):
        x = min(src.left, dst.left) - inset
        self.ax.plot([src.left, x], [src.cy, src.cy], color=EDGE, lw=1.05)
        self.ax.plot([x, x], [src.cy, dst.cy], color=EDGE, lw=1.05)
        self.arrow(x, dst.cy, dst.left, dst.cy, label, "above")

    def save(self, path: Path) -> Path:
        self.fig.tight_layout()
        self.fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(self.fig)
        return path


def _draw_fc1(out: Path) -> Path:
    """CLI + run_pipeline overview. Matches src/main.py then src/pipeline.py."""
    H = 18.6
    c = Canvas(8.6, H, "FC1 — CLI va Main Pipeline  |  nguon: src/main.py, src/pipeline.py")
    cx, w = 2.15, 5.15
    rx, rw = 7.55, 2.25

    def col(y, h, text, color, kind="round", size=7.0):
        return c.box(cx, y, w, h, text, color, kind, size)

    y = H - 0.55
    start = col(y, 0.48, "START\npython src/main.py", C_END, "terminator", 7.2)
    y -= 0.70
    parse = col(y, 0.50, "Parse CLI   _parse_args()\ncheck-env | make-sample | analyze | run", C_PROC)
    y -= 0.72
    find = col(y, 0.50, "Tim FFmpeg / FFprobe\nfind_ffmpeg_tools()", C_PROC)
    y -= 0.78
    found = col(y, 0.62, "Tim thay\nFFmpeg?", C_DEC, "diamond", 7.3)
    err2 = c.box(rx, found.y - 0.05, rw, 0.70, "log loi\nreturn 2\nEND", C_ERR, "terminator", 6.6)
    y -= 0.82
    envq = col(y, 0.62, "command ==\ncheck-env ?", C_DEC, "diamond", 7.1)
    env_end = c.box(rx, envq.y - 0.02, rw, 0.66, "In duong dan\nffmpeg/ffprobe\nreturn 0", C_END, "terminator", 6.4)
    y -= 0.80
    cfg = col(y, 0.50, "Load config\nload_config(config.yaml)", C_IO)
    y -= 0.78
    sampq = col(y, 0.62, "command ==\nmake-sample ?", C_DEC, "diamond", 7.1)
    samp_end = c.box(rx, sampq.y - 0.02, rw, 0.66, "make_sample_video\nreturn 0", C_END, "terminator", 6.4)
    y -= 0.80
    anq = col(y, 0.62, "command ==\nanalyze ?", C_DEC, "diamond", 7.1)
    an_end = c.box(rx, anq.y - 0.08, rw, 0.82, "SI/TI + ladder JSON\nKHONG encode\nKHONG VMAF\nreturn 0", C_END, "terminator", 6.2)
    y -= 0.80
    runq = col(y, 0.62, "command ==\nrun ?", C_DEC, "diamond", 7.1)
    run_end = c.box(rx, runq.y - 0.02, rw, 0.66, "Lenh khong ho tro\nreturn 1", C_ERR, "terminator", 6.4)
    y -= 0.78
    pipe = col(y, 0.50, "run_pipeline(videos, output, tools, cfg)", C_PROC)
    y -= 0.76
    empty = col(y, 0.62, "videos rong?", C_DEC, "diamond", 7.2)
    empty_err = c.box(rx, empty.y, rw, 0.62, "ValueError", C_ERR, "terminator", 6.8)
    y -= 0.78
    vmafq = col(y, 0.62, "quality.vmaf\n== false ?", C_DEC, "diamond", 7.0)
    vmaf_err = c.box(rx, vmafq.y, rw, 0.62, "RuntimeError\n(khong gia VMAF)", C_ERR, "terminator", 6.3)
    y -= 0.76
    dirs = col(y, 0.48, "Tao thu muc results/encodes/work/plots", C_IO, size=6.8)
    y -= 1.58
    body = col(
        y,
        1.32,
        "Voi MOI video\n"
        "require_file → extract_features (FFprobe, SI/TI)\n"
        "build_candidate_rungs → encode+VMAF  [FC2]\n"
        "Pareto → upper hull  [FC3]\n"
        "select_ladder_from_hull  [FC4]\n"
        "encode fixed + heuristic baseline",
        C_LOOP,
        size=6.5,
    )
    y -= 0.92
    more = col(y, 0.62, "Con video?", C_DEC, "diamond", 7.3)
    y -= 0.78
    save = col(y, 0.62, "Ghi CSV / bitrate_vmaf.csv / JSON / PNG\n(khong tao file Word)", C_IO, size=6.7)
    y -= 0.72
    outp = col(y, 0.48, "In JSON summary  |  return 0", C_IO, size=7.0)
    y -= 0.62
    end = col(y, 0.42, "END", C_END, "terminator", 7.5)

    c.down(start, parse)
    c.down(parse, find)
    c.down(find, found)
    c.right(found, err2, "NO")
    c.down(found, envq, "YES", "left")
    c.right(envq, env_end, "YES")
    c.down(envq, cfg, "NO", "left")
    c.down(cfg, sampq)
    c.right(sampq, samp_end, "YES")
    c.down(sampq, anq, "NO", "left")
    c.right(anq, an_end, "YES")
    c.down(anq, runq, "NO", "left")
    c.right(runq, run_end, "NO")
    c.down(runq, pipe, "YES", "left")
    c.down(pipe, empty)
    c.right(empty, empty_err, "YES")
    c.down(empty, vmafq, "NO", "left")
    c.right(vmafq, vmaf_err, "YES")
    c.down(vmafq, dirs, "NO", "left")
    c.down(dirs, body)
    c.down(body, more)
    c.loop_left(more, body, "YES", inset=0.52)
    c.down(more, save, "NO", "right")
    c.down(save, outp)
    c.down(outp, end)
    return c.save(out / "flowchart_1_main_pipeline.png")


def _draw_fc2(out: Path) -> Path:
    """Candidate generation + encode loop. models.py + pipeline.py + encoder + metrics."""
    H = 19.4
    c = Canvas(8.6, H, "FC2 — Candidate encoding  |  build_candidate_rungs + _encode_and_score")
    cx, w = 2.05, 5.25
    rx, rw = 7.50, 2.30

    def col(y, h, text, color, kind="round", size=7.0):
        return c.box(cx, y, w, h, text, color, kind, size)

    y = H - 0.50
    start = col(y, 0.46, "VideoMeta + AppConfig.candidates", C_IO, "terminator", 7.0)
    y -= 0.68
    gen = col(y, 0.48, "build_candidate_rungs(meta, cfg)", C_PROC)
    y -= 0.74
    empty = col(y, 0.60, "candidates YAML\nrong?", C_DEC, "diamond", 7.0)
    empty_err = c.box(rx, empty.y, rw, 0.60, "ValueError\nThieu candidates", C_ERR, "terminator", 6.3)
    y -= 0.78
    spec = col(y, 0.50, "for spec in cfg.candidates", C_LOOP, size=7.1)
    y -= 0.76
    up = col(y, 0.60, "spec.height >\nmeta.height ?", C_DEC, "diamond", 7.0)
    y -= 0.78
    br = col(y, 0.50, "for bitrate in spec.bitrates_kbps", C_LOOP, size=6.9)
    y -= 0.76
    bad = col(y, 0.60, "bitrate <= 0\nhoac trung?", C_DEC, "diamond", 7.0)
    bad_err = c.box(rx, bad.y, rw, 0.60, "ValueError", C_ERR, "terminator", 6.8)
    y -= 0.74
    add = col(y, 0.46, "append LadderRung  source='candidate'", C_PROC, size=6.8)
    y -= 0.78
    more_br = col(y, 0.58, "Con bitrate?", C_DEC, "diamond", 7.2)
    y -= 0.76
    more_sp = col(y, 0.58, "Con spec?", C_DEC, "diamond", 7.2)
    y -= 0.76
    none = col(y, 0.60, "rungs rong\nsau loc?", C_DEC, "diamond", 7.0)
    none_err = c.box(rx, none.y, rw, 0.60, "ValueError\nkhong upscale", C_ERR, "terminator", 6.3)
    y -= 0.78
    loop = col(y, 0.48, "for rung in candidates   (pipeline)", C_LOOP, size=6.9)
    y -= 0.76
    cache = col(y, 0.60, "cache hit\n(height, bitrate)?", C_DEC, "diamond", 6.9)
    y -= 0.78
    enc = col(y, 0.62, "encode_rung  libx264 -b:v\nrequire_success; size >= 100", C_PROC, size=6.7)
    enc_err = c.box(rx, enc.y, rw, 0.62, "RuntimeError\n(FFmpeg/file)", C_ERR, "terminator", 6.3)
    y -= 0.78
    qm = col(y, 0.50, "measure_quality\nPSNR, SSIM, VMAF", C_PROC, size=6.8)
    y -= 0.76
    vq = col(y, 0.60, "Parse duoc\nVMAF score?", C_DEC, "diamond", 7.0)
    v_err = c.box(rx, vq.y, rw, 0.60, "RuntimeError\n(khong gia lap)", C_ERR, "terminator", 6.3)
    y -= 0.74
    row = col(y, 0.50, "row_from → rows, candidate_rows\n(cache miss: ghi cache)", C_IO, size=6.6)
    y -= 0.76
    more_r = col(y, 0.58, "Con candidate?", C_DEC, "diamond", 7.2)
    y -= 0.68
    end = col(y, 0.44, "Sang FC3  Pareto / hull", C_END, "terminator", 7.0)

    c.down(start, gen)
    c.down(gen, empty)
    c.right(empty, empty_err, "YES")
    c.down(empty, spec, "NO", "left")
    c.down(spec, up)
    c.loop_left(up, spec, "YES skip", inset=0.78)
    c.down(up, br, "NO", "right")
    c.down(br, bad)
    c.right(bad, bad_err, "YES")
    c.down(bad, add, "NO", "left")
    c.down(add, more_br)
    c.loop_left(more_br, br, "YES", inset=0.48)
    c.down(more_br, more_sp, "NO", "right")
    c.loop_left(more_sp, spec, "YES", inset=0.78)
    c.down(more_sp, none, "NO", "right")
    c.right(none, none_err, "YES")
    c.down(none, loop, "NO", "left")
    c.down(loop, cache)
    c.down(cache, enc, "NO", "left")
    c.right(enc, enc_err, "fail")
    c.down(enc, qm)
    c.down(qm, vq)
    c.right(vq, v_err, "NO")
    c.down(vq, row, "YES", "left")
    # cache YES skips encode+measure, goes to row (quality already in cache)
    c.ax.plot([cache.right, cache.right + 0.55, cache.right + 0.55], [cache.cy, cache.cy, row.cy], color=EDGE, lw=1.05)
    c.arrow(cache.right + 0.55, row.cy, row.right, row.cy, "YES reuse", "above")
    c.down(row, more_r)
    c.loop_left(more_r, loop, "YES", inset=0.48)
    c.down(more_r, end, "NO", "right")
    return c.save(out / "flowchart_2_candidate_encoding.png")


def _draw_fc3(out: Path) -> Path:
    H = 14.8
    c = Canvas(8.4, H, "FC3 — Rate-Quality / Pareto / Upper Convex Hull  |  src/analysis/rq_points.py")
    cx, w = 2.15, 5.20
    rx, rw = 7.55, 2.22

    def col(y, h, text, color, kind="round", size=7.0):
        return c.box(cx, y, w, h, text, color, kind, size)

    y = H - 0.50
    start = col(y, 0.46, "candidate_rows  (VMAF that)", C_IO, "terminator", 7.0)
    y -= 0.70
    loop = col(y, 0.48, "for row in candidate_rows\n_rq_point(row)", C_LOOP, size=6.9)
    y -= 0.76
    none = col(y, 0.60, "row.vmaf\nis None?", C_DEC, "diamond", 7.1)
    none_err = c.box(rx, none.y, rw, 0.60, "RuntimeError", C_ERR, "terminator", 6.8)
    y -= 0.74
    rq = col(y, 0.50, "RQPoint  X=actual bitrate  Y=VMAF", C_PROC, size=6.8)
    y -= 0.70
    more = col(y, 0.56, "Con row?", C_DEC, "diamond", 7.2)
    y -= 0.76
    rem = col(
        y,
        0.78,
        "remove_dominated_points\nB dominate A neu B.bitrate<=A.bitrate\nVA B.VMAF>=A.VMAF, co strict",
        C_PROC,
        size=6.5,
    )
    y -= 0.90
    par = col(y, 0.50, "Pareto frontier\n(KHONG phai convex hull)", C_IO, size=6.9)
    y -= 0.72
    hull = col(y, 0.50, "upper_convex_hull(pareto)\nmonotone chain", C_PROC, size=6.8)
    y -= 0.72
    prep = col(y, 0.50, "Bo NaN/Inf; trung bitrate giu VMAF cao\nsort theo bitrate", C_PROC, size=6.5)
    y -= 0.76
    few = col(y, 0.60, "So diem\n<= 2 ?", C_DEC, "diamond", 7.1)
    y -= 0.80
    chain = col(y, 0.62, "Di trai → phai\npop neu cross >= 0", C_PROC, size=6.8)
    y -= 0.72
    end = col(y, 0.46, "list[RQPoint] hull  →  FC4", C_END, "terminator", 7.0)

    c.down(start, loop)
    c.down(loop, none)
    c.right(none, none_err, "YES")
    c.down(none, rq, "NO", "left")
    c.down(rq, more)
    c.loop_left(more, loop, "YES")
    c.down(more, rem, "NO", "right")
    c.down(rem, par)
    c.down(par, hull)
    c.down(hull, prep)
    c.down(prep, few)
    c.down(few, chain, "NO", "left")
    c.down(chain, end)
    # YES (<=2) skips chain
    c.ax.plot([few.right, few.right + 0.45, few.right + 0.45], [few.cy, few.cy, end.cy], color=EDGE, lw=1.05)
    c.arrow(few.right + 0.45, end.cy, end.right, end.cy, "YES", "above")
    return c.save(out / "flowchart_3_pareto_hull.png")


def _draw_fc4(out: Path) -> Path:
    H = 16.6
    c = Canvas(8.5, H, "FC4 — Hull-based ladder  |  select_ladder_from_hull + 3 phuong phap")
    cx, w = 2.05, 5.25
    rx, rw = 7.50, 2.28

    def col(y, h, text, color, kind="round", size=7.0):
        return c.box(cx, y, w, h, text, color, kind, size)

    y = H - 0.48
    start = col(y, 0.44, "hull: list[RQPoint] + meta + cfg", C_IO, "terminator", 6.9)
    y -= 0.66
    fn = col(y, 0.46, "select_ladder_from_hull(...)", C_PROC)
    y -= 0.72
    empty = col(y, 0.58, "points rong?", C_DEC, "diamond", 7.2)
    empty_err = c.box(rx, empty.y, rw, 0.58, "ValueError", C_ERR, "terminator", 6.8)
    y -= 0.72
    filt = col(y, 0.50, "Loc min_vmaf; neu rong thi giu nguyen hull", C_PROC, size=6.6)
    y -= 0.74
    one = col(y, 0.60, "prefer_one_per_height\n== true ?", C_DEC, "diamond", 6.8)
    y -= 0.78
    yes = col(y, 0.50, "1 diem / height  (VMAF max)", C_PROC, size=6.8)
    no = c.box(rx, yes.y, rw, 0.50, "sort theo bitrate", C_PROC, size=6.4)
    y -= 0.72
    mono = col(y, 0.50, "Giu TARGET bitrate tang dan\n(_ladder_bitrate, khong dung actual)", C_PROC, size=6.5)
    y -= 0.74
    m0 = col(y, 0.58, "monotonic rong?", C_DEC, "diamond", 7.1)
    m0_err = c.box(rx, m0.y, rw, 0.58, "ValueError", C_ERR, "terminator", 6.8)
    y -= 0.74
    cap = col(y, 0.58, "len > max_representations?", C_DEC, "diamond", 6.8)
    y -= 0.76
    sub = col(y, 0.48, "Subsample (max_reps=1: diem giua)", C_PROC, size=6.6)
    y -= 0.68
    rung = col(y, 0.48, "LadderRung source='hull'\nvalidate_ladder", C_PROC, size=6.7)
    y -= 0.70
    base = col(
        y,
        0.70,
        "BASELINE (khong phai PP chinh)\nbuild_fixed_ladder\nbuild_per_title_ladder(k)  heuristic",
        C_LOOP,
        size=6.4,
    )
    y -= 0.88
    enc = col(y, 0.58, "for method in hull, fixed, per_title\n_encode_and_score (cache)", C_LOOP, size=6.5)
    y -= 0.72
    more = col(y, 0.56, "Con rung / method?", C_DEC, "diamond", 6.9)
    y -= 0.68
    end = col(y, 0.44, "Hang so sanh → FC1 Save Results", C_END, "terminator", 6.7)

    c.down(start, fn)
    c.down(fn, empty)
    c.right(empty, empty_err, "YES")
    c.down(empty, filt, "NO", "left")
    c.down(filt, one)
    c.down(one, yes, "YES", "left")
    c.right(one, no, "NO")
    c.arrow(no.left, no.bot, mono.right - 0.4, mono.top, "", "right")
    c.down(yes, mono)
    c.down(mono, m0)
    c.right(m0, m0_err, "YES")
    c.down(m0, cap, "NO", "left")
    c.down(cap, sub, "YES", "left")
    c.down(sub, rung)
    c.ax.plot([cap.right, cap.right + 0.4, cap.right + 0.4], [cap.cy, cap.cy, rung.cy], color=EDGE, lw=1.05)
    c.arrow(cap.right + 0.4, rung.cy, rung.right, rung.cy, "NO", "above")
    c.down(rung, base)
    c.down(base, enc)
    c.down(enc, more)
    c.loop_left(more, enc, "YES")
    c.down(more, end, "NO", "right")
    return c.save(out / "flowchart_4_ladder_selection.png")


def draw_all(out_dir: Path | None = None) -> list[Path]:
    out = out_dir or OUT
    out.mkdir(parents=True, exist_ok=True)
    return [_draw_fc1(out), _draw_fc2(out), _draw_fc3(out), _draw_fc4(out)]


if __name__ == "__main__":
    for p in draw_all():
        print(p)
