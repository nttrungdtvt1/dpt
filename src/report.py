"""Tao bao cao Markdown tong hop ket qua thi nghiem per-title encoding.

Bao cao gom:
  1. Thong tin video dau vao
  2. SI/TI content characterization
  3. Bang ket qua candidates (target bitrate, actual bitrate, VMAF, ...)
  4. Pareto frontier
  5. Proposed (hull-based) ladder
  6. Fixed ladder baseline
  7. So sanh KPI
  8. Dien giai
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(v: Any, decimals: int = 3) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    col_w = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_w):
                col_w[i] = max(col_w[i], len(cell))
    sep = "| " + " | ".join("-" * w for w in col_w) + " |"
    header_row = "| " + " | ".join(h.ljust(col_w[i]) for i, h in enumerate(headers)) + " |"
    lines = [header_row, sep]
    for row in rows:
        line = "| " + " | ".join(str(row[i]).ljust(col_w[i]) if i < len(col_w) else str(row[i]) for i in range(len(col_w))) + " |"
        lines.append(line)
    return "\n".join(lines)


def _bytes_to_mb(b: int) -> float:
    return b / (1024 * 1024)


def _bytes_to_kb(b: int) -> float:
    return b / 1024


# ---------------------------------------------------------------------------
# KPI computation
# ---------------------------------------------------------------------------

def compute_kpi(analyses: list[dict[str, Any]], rows_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Tinh KPI so sanh giua hull ladder, fixed ladder va per_title heuristic."""
    results = []
    for analysis in analyses:
        video = analysis.get("video", "?")
        # Lay rows thuoc video nay
        video_rows = [r for r in rows_data if r.get("video") == video]

        def _get_rows(method: str) -> list[dict[str, Any]]:
            return [r for r in video_rows if r.get("method") == method]

        hull_rows = _get_rows("hull")
        fixed_rows = _get_rows("fixed")
        pt_rows = _get_rows("per_title")
        candidate_rows = _get_rows("candidate")

        def _avg_bitrate(rws: list[dict]) -> float | None:
            if not rws:
                return None
            return sum(r.get("actual_bitrate_kbps", 0) for r in rws) / len(rws)

        def _total_size_mb(rws: list[dict]) -> float | None:
            if not rws:
                return None
            return sum(r.get("size_bytes", 0) for r in rws) / (1024 * 1024)

        def _avg_vmaf(rws: list[dict]) -> float | None:
            vals = [r.get("vmaf") for r in rws if r.get("vmaf") is not None]
            return sum(vals) / len(vals) if vals else None

        hull_avg_br = _avg_bitrate(hull_rows)
        fixed_avg_br = _avg_bitrate(fixed_rows)
        hull_avg_vmaf = _avg_vmaf(hull_rows)
        fixed_avg_vmaf = _avg_vmaf(fixed_rows)
        hull_total_mb = _total_size_mb(hull_rows)
        fixed_total_mb = _total_size_mb(fixed_rows)
        pt_avg_br = _avg_bitrate(pt_rows)
        pt_avg_vmaf = _avg_vmaf(pt_rows)
        pt_total_mb = _total_size_mb(pt_rows)

        # Bitrate saving: so sanh avg bitrate giua hull va fixed
        # Cach tinh: (fixed_avg - hull_avg) / fixed_avg * 100
        # Chi tinh duoc neu ca hai co data
        bitrate_saving_pct = None
        if hull_avg_br is not None and fixed_avg_br and fixed_avg_br > 0:
            bitrate_saving_pct = (fixed_avg_br - hull_avg_br) / fixed_avg_br * 100

        # Delta VMAF: hull - fixed (positive = hull chat luong cao hon)
        # Match theo height cung nhau (best effort)
        delta_vmaf_matched = _compute_delta_vmaf_matched(hull_rows, fixed_rows)

        results.append({
            "video": video,
            "width": analysis.get("width"),
            "height": analysis.get("height"),
            "duration": analysis.get("duration_seconds"),
            "fps": analysis.get("fps"),
            "codec": analysis.get("source_codec"),
            "si": analysis.get("si"),
            "ti": analysis.get("ti"),
            "complexity_index": analysis.get("complexity_index"),
            "complexity_label": analysis.get("complexity_label"),
            "n_candidates": len(candidate_rows),
            "n_pareto": len(analysis.get("pareto") or []),
            "n_hull": len(analysis.get("convex_hull") or []),
            "hull": {
                "n_rungs": len(hull_rows),
                "avg_bitrate_kbps": hull_avg_br,
                "avg_vmaf": hull_avg_vmaf,
                "total_size_mb": hull_total_mb,
                "rows": hull_rows,
            },
            "fixed": {
                "n_rungs": len(fixed_rows),
                "avg_bitrate_kbps": fixed_avg_br,
                "avg_vmaf": fixed_avg_vmaf,
                "total_size_mb": fixed_total_mb,
                "rows": fixed_rows,
            },
            "per_title": {
                "n_rungs": len(pt_rows),
                "avg_bitrate_kbps": pt_avg_br,
                "avg_vmaf": pt_avg_vmaf,
                "total_size_mb": pt_total_mb,
                "rows": pt_rows,
            },
            "pareto": analysis.get("pareto") or [],
            "convex_hull": analysis.get("convex_hull") or [],
            "hull_ladder_def": analysis.get("hull_ladder") or [],
            "fixed_ladder_def": analysis.get("fixed_ladder") or [],
            "candidate_rows": candidate_rows,
            "bitrate_saving_pct": bitrate_saving_pct,
            "delta_vmaf_matched": delta_vmaf_matched,
            "ladder_selection_note": analysis.get("content_complexity_role", ""),
        })
    return results


def _compute_delta_vmaf_matched(
    hull_rows: list[dict], fixed_rows: list[dict]
) -> list[dict[str, Any]]:
    """Ghep cac rung cung height giua hull va fixed, tinh delta VMAF.

    Phuong phap ghep: theo height (do phan giai). Neu hai ladder co cac
    height khac nhau hoan toan, tra ve danh sach rong.
    """
    hull_by_height: dict[int, dict] = {}
    for r in hull_rows:
        h = r.get("height")
        if h is not None:
            hull_by_height[h] = r
    fixed_by_height: dict[int, dict] = {}
    for r in fixed_rows:
        h = r.get("height")
        if h is not None:
            fixed_by_height[h] = r
    common_heights = sorted(set(hull_by_height) & set(fixed_by_height))
    result = []
    for h in common_heights:
        hrow = hull_by_height[h]
        frow = fixed_by_height[h]
        hv = hrow.get("vmaf")
        fv = frow.get("vmaf")
        result.append({
            "height": h,
            "hull_vmaf": hv,
            "fixed_vmaf": fv,
            "delta_vmaf": (hv - fv) if (hv is not None and fv is not None) else None,
            "hull_bitrate": hrow.get("actual_bitrate_kbps"),
            "fixed_bitrate": frow.get("actual_bitrate_kbps"),
        })
    return result


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _section_env(tools_info: dict[str, str] | None = None) -> str:
    lines = ["## 0. Thong tin moi truong\n"]
    if tools_info:
        for k, v in tools_info.items():
            lines.append(f"- **{k}**: `{v}`")
    else:
        lines.append("- FFmpeg/FFprobe: da kiem tra truoc khi chay pipeline.")
    lines.append("\n- libvmaf: **co** (FFmpeg full_build Gyan.dev)")
    return "\n".join(lines)


def _section_input(kpi: dict[str, Any]) -> str:
    lines = [
        f"## 1. Video dau vao: `{kpi['video']}`\n",
        f"| Thuoc tinh | Gia tri |",
        f"|---|---|",
        f"| Filename | `{kpi['video']}` |",
        f"| Resolution | {kpi['width']}x{kpi['height']} |",
        f"| Duration | {_fmt(kpi['duration'], 3)} s |",
        f"| FPS | {_fmt(kpi['fps'], 3)} |",
        f"| Codec | {kpi['codec'] or 'N/A'} |",
    ]
    dur = kpi.get("duration") or 0
    if dur < 10 or dur > 30:
        lines.append(f"\n> **Canh bao**: Duration {_fmt(dur, 1)}s nam ngoai khoan khuyen nghi 10-30s.")
    return "\n".join(lines)


def _section_siti(kpi: dict[str, Any]) -> str:
    si = kpi.get("si")
    ti = kpi.get("ti")
    idx = kpi.get("complexity_index")
    label = kpi.get("complexity_label", "?")
    lines = [
        "## 2. Content Characterization (SI/TI)\n",
        "SI/TI mo ta do phuc tap noi dung video. Chung **khong truc tiep** quyet dinh bitrate ladder.",
        "Trong pipeline nay, SI/TI duoc tinh bang Sobel spatial std va frame-diff temporal std,",
        "lay median tren cac frame mau.\n",
        f"| Chi so | Gia tri |",
        f"|---|---|",
        f"| Spatial Information (SI) | {_fmt(si, 4)} |",
        f"| Temporal Information (TI) | {_fmt(ti, 4)} |",
        f"| Complexity Index | {_fmt(idx, 4)} |",
        f"| Label | **{label}** |",
        "",
        "**Dien giai**:",
        f"- SI={_fmt(si,1)}: {'Noi dung phuc tap ve khong gian (nhieu detail, texture)' if (si or 0) > 50 else 'Noi dung don gian ve khong gian (it detail, flat areas)'}",
        f"- TI={_fmt(ti,1)}: {'Chuyen dong manh, thay doi nhieu giua cac frame' if (ti or 0) > 20 else 'It chuyen dong, scene tuong doi tinh'}",
        f"- Label=**{label}**: dung cho heuristic k-scaling (k*fixed ladder), KHONG phai cho hull-based selection.",
    ]
    return "\n".join(lines)


def _section_candidates(kpi: dict[str, Any]) -> str:
    rows = kpi.get("candidate_rows", [])
    lines = [
        f"## 3. Ket qua Candidate Encoding ({len(rows)} candidates)\n",
        "Moi candidate la mot cap (resolution, target_bitrate). Actual bitrate duoc do sau khi encode.\n",
    ]
    headers = ["Rung", "Resolution", "Target (kbps)", "Actual (kbps)", "File (KB)", "VMAF (Mean)", "VMAF Min", "VMAF Max", "PSNR"]
    table_rows = []
    for r in sorted(rows, key=lambda x: (x.get("height", 0), x.get("target_bitrate_kbps", 0))):
        table_rows.append([
            str(r.get("rung", "")),
            f"{r.get('width')}x{r.get('height')}",
            _fmt(r.get("target_bitrate_kbps"), 0),
            _fmt(r.get("actual_bitrate_kbps"), 1),
            _fmt(_bytes_to_kb(r.get("size_bytes", 0)), 1),
            _fmt(r.get("vmaf"), 3),
            _fmt(r.get("vmaf_min"), 3),
            _fmt(r.get("vmaf_max"), 3),
            _fmt(r.get("psnr"), 3),
        ])
    lines.append(_md_table(headers, table_rows))
    lines.append("\n> **Luu y**: Actual bitrate = file_size * 8 / duration (kbps), do bang FFprobe sau encode.")
    lines.append("> Target bitrate chi la cap dat, khong phai ket qua thuc te.")
    return "\n".join(lines)


def _section_pareto(kpi: dict[str, Any]) -> str:
    pareto = kpi.get("pareto", [])
    hull = kpi.get("convex_hull", [])
    lines = [
        f"## 4. Pareto Frontier va Upper Convex Hull\n",
        "**Pareto filtering** loai bo cac candidate bi dominated:",
        "- A dominates B neu: A.actual_bitrate <= B.actual_bitrate VA A.vmaf >= B.vmaf",
        "  (va it nhat mot dieu kien la strict).\n",
        f"Tong candidates: {len(kpi.get('candidate_rows', []))}, Pareto: {len(pareto)}, Hull: {len(hull)}\n",
    ]
    if pareto:
        headers = ["Rung", "Actual (kbps)", "VMAF"]
        rows = []
        for p in sorted(pareto, key=lambda x: x.get("bitrate_kbps", 0)):
            rows.append([
                str(p.get("rung_name", f"{p.get('height')}p")),
                _fmt(p.get("bitrate_kbps"), 1),
                _fmt(p.get("vmaf"), 3),
            ])
        lines.append("### Pareto Frontier\n")
        lines.append(_md_table(headers, rows))
    if hull:
        lines.append("\n### Upper Convex Hull\n")
        lines.append("Hull la duong bao lo (convex envelope) phia tren cua Pareto trong khong gian bitrate-VMAF.")
        lines.append("Hull KHONG dong nghia voi Pareto.\n")
        headers = ["Rung", "Actual (kbps)", "VMAF"]
        rows = []
        for p in sorted(hull, key=lambda x: x.get("bitrate_kbps", 0)):
            rows.append([
                str(p.get("rung_name", f"{p.get('height')}p")),
                _fmt(p.get("bitrate_kbps"), 1),
                _fmt(p.get("vmaf"), 3),
            ])
        lines.append(_md_table(headers, rows))
    return "\n".join(lines)


def _section_hull_ladder(kpi: dict[str, Any]) -> str:
    hull_data = kpi.get("hull", {})
    ladder_def = kpi.get("hull_ladder_def", [])
    rows_enc = hull_data.get("rows", [])
    lines = [
        "## 5. Proposed Per-Title Ladder (Hull-Based)\n",
        "**Quy tac chon ladder tu hull** (Pipeline chinh):\n",
        "1. Tinh Pareto frontier tu candidate encoding grid.",
        "2. Lay upper convex hull cua Pareto (efficient frontier).",
        "3. Ap dung rang buoc tu config: `max_representations`, `prefer_one_per_height`, `min_vmaf`.",
        "4. Dam bao bitrate tang dan.\n",
        "Day la phuong phap **dinh luong, co the tai lap**: khong chon thu cong bang mat.",
        "Tham so rule nam trong `config/config.yaml` (ladder_selection).\n",
    ]
    if rows_enc:
        headers = ["Rung", "Resolution", "Target (kbps)", "Actual (kbps)", "VMAF", "PSNR"]
        rows = []
        for r in sorted(rows_enc, key=lambda x: x.get("height", 0)):
            rows.append([
                str(r.get("rung", "")),
                f"{r.get('width')}x{r.get('height')}",
                _fmt(r.get("target_bitrate_kbps"), 0),
                _fmt(r.get("actual_bitrate_kbps"), 1),
                _fmt(r.get("vmaf"), 3),
                _fmt(r.get("psnr"), 3),
            ])
        lines.append(_md_table(headers, rows))
    elif ladder_def:
        headers = ["Name", "Width", "Height", "Bitrate (kbps)"]
        rows = [[d.get("name", ""), str(d.get("width", "")), str(d.get("height", "")), str(d.get("bitrate_kbps", ""))] for d in ladder_def]
        lines.append(_md_table(headers, rows))
    avg_br = hull_data.get("avg_bitrate_kbps")
    avg_vmaf = hull_data.get("avg_vmaf")
    total_mb = hull_data.get("total_size_mb")
    n = hull_data.get("n_rungs", 0)
    lines.append(f"\n**Summary**: {n} rung | Avg bitrate: {_fmt(avg_br, 1)} kbps | Avg VMAF: {_fmt(avg_vmaf, 3)} | Total: {_fmt(total_mb, 3)} MB")
    return "\n".join(lines)


def _section_fixed_ladder(kpi: dict[str, Any]) -> str:
    fixed_data = kpi.get("fixed", {})
    rows_enc = fixed_data.get("rows", [])
    lines = [
        "## 6. Fixed Ladder Baseline\n",
        "Fixed ladder la baseline **khong phu thuoc noi dung**: cac bac duoc dinh nghia truoc trong config,",
        "khong thay doi theo video. Day la diem so sanh de danh gia hieu qua cua per-title approach.\n",
    ]
    if rows_enc:
        headers = ["Rung", "Resolution", "Target (kbps)", "Actual (kbps)", "VMAF", "PSNR"]
        rows = []
        for r in sorted(rows_enc, key=lambda x: x.get("height", 0)):
            rows.append([
                str(r.get("rung", "")),
                f"{r.get('width')}x{r.get('height')}",
                _fmt(r.get("target_bitrate_kbps"), 0),
                _fmt(r.get("actual_bitrate_kbps"), 1),
                _fmt(r.get("vmaf"), 3),
                _fmt(r.get("psnr"), 3),
            ])
        lines.append(_md_table(headers, rows))
    avg_br = fixed_data.get("avg_bitrate_kbps")
    avg_vmaf = fixed_data.get("avg_vmaf")
    total_mb = fixed_data.get("total_size_mb")
    n = fixed_data.get("n_rungs", 0)
    lines.append(f"\n**Summary**: {n} rung | Avg bitrate: {_fmt(avg_br, 1)} kbps | Avg VMAF: {_fmt(avg_vmaf, 3)} | Total: {_fmt(total_mb, 3)} MB")
    return "\n".join(lines)


def _section_comparison(kpi: dict[str, Any]) -> str:
    hull = kpi.get("hull", {})
    fixed = kpi.get("fixed", {})
    pt = kpi.get("per_title", {})
    saving = kpi.get("bitrate_saving_pct")
    delta_matched = kpi.get("delta_vmaf_matched", [])

    lines = [
        "## 7. So sanh KPI: Hull vs Fixed vs Heuristic\n",
        "**Phuong phap so sanh bitrate**: trung binh actual_bitrate_kbps theo so bac cua moi ladder.",
        "Day khong phai BD-Rate nhung du y nghia cho demo sinh vien.\n",
        "**Phuong phap so sanh VMAF**: ghep cac bac cung height giua hull va fixed, tinh delta VMAF.",
        "Neu hai ladder khong co chung height nao, delta VMAF khong tinh duoc.\n",
    ]

    # Bang tong hop
    headers = ["KPI", "Hull (per-title)", "Fixed (baseline)", "Heuristic (k*fixed)", "Ghi chu"]
    rows = [
        [
            "So rung",
            str(hull.get("n_rungs", 0)),
            str(fixed.get("n_rungs", 0)),
            str(pt.get("n_rungs", 0)),
            "",
        ],
        [
            "Avg bitrate (kbps)",
            _fmt(hull.get("avg_bitrate_kbps"), 1),
            _fmt(fixed.get("avg_bitrate_kbps"), 1),
            _fmt(pt.get("avg_bitrate_kbps"), 1),
            "Actual, trung binh cac bac",
        ],
        [
            "Avg VMAF",
            _fmt(hull.get("avg_vmaf"), 3),
            _fmt(fixed.get("avg_vmaf"), 3),
            _fmt(pt.get("avg_vmaf"), 3),
            "",
        ],
        [
            "Total size (MB)",
            _fmt(hull.get("total_size_mb"), 3),
            _fmt(fixed.get("total_size_mb"), 3),
            _fmt(pt.get("total_size_mb"), 3),
            "Tong kich thuoc tat ca bac",
        ],
        [
            "Bitrate saving",
            _fmt(saving, 2) + "%" if saving is not None else "N/A",
            "baseline",
            "N/A",
            "(fixed_avg - hull_avg)/fixed_avg",
        ],
    ]
    lines.append(_md_table(headers, rows))

    # Delta VMAF matched
    if delta_matched:
        lines.append("\n### Delta VMAF (ghep theo height)\n")
        dh = ["Height", "Hull VMAF", "Fixed VMAF", "ΔVMAF (hull - fixed)"]
        dr = []
        for item in delta_matched:
            dr.append([
                f"{item['height']}p",
                _fmt(item.get("hull_vmaf"), 3),
                _fmt(item.get("fixed_vmaf"), 3),
                _fmt(item.get("delta_vmaf"), 4),
            ])
        lines.append(_md_table(dh, dr))
    else:
        lines.append("\n> **Luu y**: Hull va fixed ladder khong chia se cung height → khong tinh duoc delta VMAF theo matching. Dung avg VMAF de so sanh.")

    # Bitrate saving interpretation
    if saving is not None:
        if saving > 0:
            lines.append(f"\n**Bitrate saving: {_fmt(saving, 2)}%** – Hull ladder tiet kiem bitrate so voi fixed ladder tren video nay.")
        elif saving < 0:
            lines.append(f"\n**Bitrate overhead: {_fmt(-saving, 2)}%** – Hull ladder dung nhieu bitrate hon fixed tren video nay.")
        else:
            lines.append(f"\n**Bitrate saving: 0%** – Hai ladder co bitrate tuong duong.")

    return "\n".join(lines)


def _section_interpretation(kpi: dict[str, Any]) -> str:
    pareto = kpi.get("pareto", [])
    cands = kpi.get("candidate_rows", [])
    dominated = len(cands) - len(pareto)
    hull = kpi.get("convex_hull", [])
    saving = kpi.get("bitrate_saving_pct")
    label = kpi.get("complexity_label", "?")

    lines = [
        "## 8. Dien giai ket qua\n",
        f"### 8.1 Candidate filtering\n",
        f"- Tong candidates duoc encode: **{len(cands)}**",
        f"- Candidates bi dominated (loai): **{dominated}**",
        f"- Candidates trong Pareto frontier: **{len(pareto)}**",
        f"- Diem tren Upper Convex Hull: **{len(hull)}**\n",
    ]

    # Giai thich dominated
    if dominated > 0:
        lines.append("Mot candidate bi loai khi co candidate khac co:")
        lines.append("bitrate nho hon hoang bam va VMAF cao hon hoac bang.")
        lines.append("Vi du: neu 360p@500k co VMAF tuong tu 360p@700k, thi 360p@700k bi loai.\n")

    lines.append("### 8.2 Tu Pareto den Ladder\n")
    lines.append("Pareto frontier KHONG thi dong nghia voi bitrate ladder cuoi cung.")
    lines.append("Ladder selection ap dung them rang buoc:")
    lines.append("- `prefer_one_per_height = true`: moi do phan giai giu mot bac (VMAF cao nhat, bitrate thap nhat).")
    lines.append("- `max_representations`: gioi han so bac toi da.")
    lines.append("- Bitrate tang dan (monotonic constraint).\n")

    lines.append("### 8.3 Per-title vs Fixed tren video nay\n")
    if saving is not None:
        if saving > 5:
            lines.append(f"**Ket qua tren video nay**: hull ladder tiet kiem khoang {_fmt(saving, 1)}% bitrate so voi fixed.")
            lines.append("Dieu nay phu hop voi noi dung complexity={label}: video {('de' if label == 'easy' else 'kho' if label == 'hard' else 'trung binh')} co the encode hieu qua hon.")
        elif saving < -5:
            lines.append(f"**Ket qua tren video nay**: hull ladder dung nhieu hon fixed {_fmt(-saving, 1)}% bitrate.")
            lines.append("Dieu nay co the do hull chon bac co chatluong cao hon (VMAF cao hon).")
        else:
            lines.append(f"**Ket qua tren video nay**: hull va fixed co bitrate tuong duong ({_fmt(abs(saving) if saving else 0, 1)}% chenh lech).")

    lines.append("")
    lines.append("> **Chu y quan trong**: Ket luan nay chi ap dung cho video cu the nay.")
    lines.append("> Khong the ket luan chung rang per-title encoding 'luon luon tot hon' fixed ladder.")
    lines.append("> Can thu nghiem tren nhieu video voi noi dung da dang de co ket luan tong quat.")

    return "\n".join(lines)


def _section_outputs() -> str:
    return textwrap.dedent("""\
    ## 9. File output

    | File | Mo ta |
    |---|---|
    | `results/experiment_results.csv` | Toan bo rows: candidates + fixed + hull + per_title |
    | `results/bitrate_vmaf.csv` | Chi candidates (cho ve duong curve) |
    | `results/experiment_results.json` | Du lieu day du (JSON) |
    | `results/pareto.csv` | Pareto frontier cua tung video |
    | `results/proposed_ladder.csv` | Hull-based proposed ladder |
    | `results/plots/bitrate_vmaf.png` | Duong Bitrate–VMAF + Pareto + Hull |
    | `results/plots/bitrate_ssim.png` | Duong Bitrate–SSIM |
    | `results/plots/file_size_by_rung.png` | Dung luong theo bac |
    | `results/plots/ladder_total_size.png` | Tong dung luong theo phuong phap |
    | `results/report/results.md` | Bao cao nay |
    """)


# ---------------------------------------------------------------------------
# Main report builder
# ---------------------------------------------------------------------------

def build_report(
    analyses: list[dict[str, Any]],
    rows_data: list[dict[str, Any]],
    output_path: Path,
    tools_info: dict[str, str] | None = None,
) -> Path:
    """Tao file report Markdown va luu vao output_path."""
    kpis = compute_kpi(analyses, rows_data)
    sections: list[str] = [
        "# Ket qua Thi nghiem: Per-Title Bitrate Ladder Selection\n",
        "> Bao cao tu dong tao boi pipeline. So lieu lay truc tiep tu encode va VMAF thuc te.\n",
        _section_env(tools_info),
        "",
    ]
    for kpi in kpis:
        sections.extend([
            "---\n",
            _section_input(kpi),
            "",
            _section_siti(kpi),
            "",
            _section_candidates(kpi),
            "",
            _section_pareto(kpi),
            "",
            _section_hull_ladder(kpi),
            "",
            _section_fixed_ladder(kpi),
            "",
            _section_comparison(kpi),
            "",
            _section_interpretation(kpi),
            "",
        ])
    sections.append(_section_outputs())
    sections.append("\n---\n*Bao cao duoc tao tu dong. KHONG chinh sua ket qua thu cong.*\n")
    content = "\n".join(sections)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_pareto_csv(analyses: list[dict[str, Any]], output_path: Path) -> Path:
    """Xuat Pareto frontier cua tung video ra CSV."""
    import csv
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["video", "rung_name", "height", "width", "bitrate_kbps", "vmaf", "psnr", "ssim", "size_bytes"]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for analysis in analyses:
            video = analysis.get("video", "?")
            for p in analysis.get("pareto") or []:
                writer.writerow({
                    "video": video,
                    "rung_name": p.get("rung_name", ""),
                    "height": p.get("height", ""),
                    "width": p.get("width", ""),
                    "bitrate_kbps": round(p.get("bitrate_kbps", 0), 3),
                    "vmaf": round(p.get("vmaf", 0), 6) if p.get("vmaf") is not None else "",
                    "psnr": round(p.get("psnr", 0), 3) if p.get("psnr") is not None else "",
                    "ssim": round(p.get("ssim", 0), 6) if p.get("ssim") is not None else "",
                    "size_bytes": p.get("size_bytes", ""),
                })
    return output_path


def write_proposed_ladder_csv(analyses: list[dict[str, Any]], output_path: Path) -> Path:
    """Xuat hull-based proposed ladder ra CSV."""
    import csv
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["video", "name", "width", "height", "bitrate_kbps", "source"]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for analysis in analyses:
            video = analysis.get("video", "?")
            for rung in analysis.get("hull_ladder") or []:
                writer.writerow({
                    "video": video,
                    "name": rung.get("name", ""),
                    "width": rung.get("width", ""),
                    "height": rung.get("height", ""),
                    "bitrate_kbps": rung.get("bitrate_kbps", ""),
                    "source": rung.get("source", "hull"),
                })
    return output_path
