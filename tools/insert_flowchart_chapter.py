"""Insert a flowchart chapter into the EXISTING code-explanation DOCX.

Does not rebuild the document. Draws flowcharts from the real call flow, then
inserts them after chapter 4 (before '5. Cấu trúc thư mục').
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import build_code_explanation as exp  # noqa: E402
from draw_flowcharts import draw_all  # noqa: E402

DOCX = ROOT / "docs" / "Per_Title_Encoding_Code_Explanation.docx"
MARKER = "5. Cấu trúc thư mục"
CHAPTER = "4A. FLOWCHART THUẬT TOÁN VÀ LIÊN KẾT VỚI MÃ NGUỒN"


def _heading(doc, text, level):
    exp.heading(doc, text, level)


def _para(doc, text, **kw):
    exp.para(doc, text, **kw)


def _note(doc, kind, text):
    exp.note(doc, kind, text)


def _code(doc, text, caption=None):
    exp.code_block(doc, text, caption)


def _table(doc, headers, rows, title):
    exp.add_table(doc, headers, rows, title)


def _picture(doc, path, title):
    exp.picture(doc, path, title)


def _remove_existing_chapter(doc) -> None:
    start = None
    end = None
    for para in doc.paragraphs:
        if para.text.strip().startswith("4A. FLOWCHART"):
            start = para._element
        if start is not None and para.text.strip() == MARKER:
            end = para._element
            break
    if start is None:
        return
    el = start
    while el is not None and el is not end:
        nxt = el.getnext()
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)
        el = nxt


def add_flowchart_chapter(doc: Document, images: dict[str, Path]) -> None:
    _heading(doc, CHAPTER, 1)
    _note(
        doc,
        "Nguồn lưu đồ",
        "Lưu đồ được xây dựng dựa trên mã nguồn thực tế của project "
        "(src/main.py, src/pipeline.py và các module được gọi). Không lấy sơ đồ trên Internet. "
        "Không vẽ pipeline lý tưởng nếu code không chạy như vậy.",
    )
    _para(
        doc,
        "Chương này phục vụ bảo vệ: khi giảng viên chỉ một khối trên Flowchart, sinh viên trả lời "
        "khối làm gì, dữ liệu vào/ra, file, function, đoạn code, và vì sao bước đó đứng trước bước sau. "
        "Các chương 5–26 phía sau giữ nguyên nội dung đã có.",
        indent=False,
    )

    _heading(doc, "4A.1. Flowchart 1 — CLI và Main Pipeline", 2)
    _para(
        doc,
        "Điểm vào thật là hàm main() trong src/main.py, không phải run_pipeline. "
        "find_ffmpeg_tools() chạy trước load_config. Lệnh analyze không encode và không đo VMAF; "
        "chỉ lệnh run mới chạy pipeline hull-based. tools/build_report.py không được gọi trong pipeline.",
    )
    _picture(
        doc,
        images["main"],
        "Hình F.1. Flowchart tổng thể — main() và run_pipeline (code thực tế)",
    )
    _para(
        doc,
        "Đầu vào: danh sách Path video (args.videos) và --output (mặc định results). "
        "Đầu ra của lệnh run: experiment_results.csv/.json, bitrate_vmaf.csv, PNG, file mp4 trong results/encodes/, "
        "JSON summary in ra stdout.",
    )

    _heading(doc, "4A.2. Flowchart 2 — Candidate Encoding", 2)
    _para(
        doc,
        "Lưới candidate đến từ YAML (AppConfig.candidates), không hard-code trong Python. "
        "Số vòng lặp = số LadderRung sau khi lọc không upscale. Ví dụ nguồn 720p và config 4 height: "
        "1080p bị continue, còn 360/432/720 × nhiều bitrate (lần thí nghiệm: 12 candidate/video).",
    )
    _picture(
        doc,
        images["candidate"],
        "Hình F.2. Flowchart candidate: lọc YAML, encode, đo chất lượng, cache",
    )

    _heading(doc, "4A.3. Flowchart 3 — Rate–Quality / Pareto / Upper Convex Hull", 2)
    _para(
        doc,
        "Thứ tự trong pipeline.py là bắt buộc: rq_points → pareto_frontier → upper_convex_hull. "
        "pareto_frontier chỉ gọi remove_dominated_points; không phải hull. "
        "upper_convex_hull dùng monotone chain trên (actual bitrate, VMAF).",
    )
    _picture(
        doc,
        images["pareto"],
        "Hình F.3. Flowchart Pareto rồi upper convex hull — hai khối khác nhau",
    )

    _heading(doc, "4A.4. Flowchart 4 — Hull-based Per-Title Ladder Selection", 2)
    _para(
        doc,
        "select_ladder_from_hull không lấy hết điểm hull. Ràng buộc YAML: min_vmaf, prefer_one_per_height, "
        "max_representations. Bitrate monotonic dùng target_bitrate_kbps vì actual có thể sụp trên nội dung dễ nén.",
    )
    _picture(
        doc,
        images["ladder"],
        "Hình F.4. Flowchart select_ladder_from_hull và so sánh 3 phương pháp",
    )

    _heading(doc, "4A.5. Bảng mapping Flowchart → mã nguồn", 2)
    _table(
        doc,
        ["STT", "Khối Flowchart", "Vai trò", "File nguồn", "Function/Class", "Đoạn then chốt"],
        [
            ["1", "START / CLI", "Parse lệnh, tìm FFmpeg", "src/main.py", "main, _parse_args", "find_ffmpeg_tools(); dest=command"],
            ["2", "Load config", "Đọc YAML", "src/config.py", "load_config, AppConfig", "candidates, quality.vmaf, fixed_ladder"],
            ["3", "FFprobe", "Metadata nguồn", "src/analyzer/video_probe.py", "probe_video, VideoMeta", "ffprobe -print_format json"],
            ["4", "Validate video", "Cấm clip quá nhỏ/ngắn", "src/analyzer/feature_extractor.py", "extract_features", "width<16; duration<=0.2"],
            ["5", "SI/TI", "Mô tả phức tạp; k heuristic", "src/analyzer/complexity.py", "analyze_complexity", "Sobel SI, frame-diff TI"],
            ["6", "Candidate generation", "Lưới height × bitrate", "src/ladder/models.py", "build_candidate_rungs", "if spec.height > meta.height: continue"],
            ["7", "Loop candidate", "Encode từng điểm", "src/pipeline.py", "run_pipeline", "for rung in candidates"],
            ["8", "Cache encode", "Tránh encode trùng height+bitrate", "src/pipeline.py", "_encode_and_score", "cache.get((height, bitrate))"],
            ["9", "FFmpeg Encode", "libx264 ABR", "src/encoder/ffmpeg_encoder.py", "encode_rung, _base_args", "require_success; size<100"],
            ["10", "VMAF/PSNR/SSIM", "Đo full-reference", "src/metrics/quality_metrics.py", "measure_quality, parse_vmaf_score", "libvmaf; raise nếu thiếu VMAF"],
            ["11", "Collect row", "Một encode → một dòng", "src/metrics/result_collector.py", "row_from, ExperimentRow", "method='candidate'"],
            ["12", "RQPoint", "Dataset bitrate–VMAF", "src/pipeline.py, src/analysis/rq_points.py", "_rq_point, RQPoint", "raise nếu vmaf is None"],
            ["13", "Remove dominated / Pareto", "Min bitrate, max VMAF", "src/analysis/rq_points.py", "remove_dominated_points, pareto_frontier", "strict inequality"],
            ["14", "Upper convex hull", "Envelope lồi", "src/analysis/rq_points.py", "upper_convex_hull", "monotone chain, cross>=0 pop"],
            ["15", "Ladder selection", "Hull → ABR thực dụng", "src/ladder/models.py", "select_ladder_from_hull", "one-per-height; target monotonic"],
            ["16", "Validate ladder", "Chẵn, không upscale, bitrate tăng", "src/ladder/models.py", "validate_ladder", "ValueError nếu vi phạm"],
            ["17", "Fixed + heuristic", "Hai baseline", "src/ladder/models.py", "build_fixed_ladder, build_per_title_ladder", "k × fixed; KHÔNG xóa heuristic"],
            ["18", "So sánh 3 PP", "Encode hull/fixed/per_title", "src/pipeline.py", "run_pipeline", "for method, ladder, method_dir in ladders"],
            ["19", "Output", "CSV/JSON/PNG", "result_collector.py, plots.py, pipeline.py", "write_csv, write_json, plot_results, _write_bitrate_vmaf_csv", "bitrate_vmaf.png + 3 plot cũ"],
            ["20", "FFmpeg lỗi", "Dừng, không nuốt lỗi", "src/utils/ffmpeg_tools.py", "require_success", "returncode != 0 → RuntimeError"],
        ],
        "Bảng F.1. Mapping khối Flowchart với file/function thực tế",
    )

    _heading(doc, "4A.6. Trích đoạn code thực tế theo khối", 2)

    _heading(doc, "Khối: START / rẽ nhánh CLI", 3)
    _code(
        doc,
        "tools = find_ffmpeg_tools()\n"
        "...\n"
        "if args.command == \"run\":\n"
        "    summary = run_pipeline(args.videos, args.output, tools, cfg)\n"
        "    print(json.dumps(summary, indent=2, ensure_ascii=False))\n"
        "    return 0",
        "src/main.py — main()",
    )
    _para(
        doc,
        "Đoạn code này thực hiện: tìm ffmpeg/ffprobe; nếu lệnh là run thì gọi pipeline và in summary. "
        "Trong Flowchart: khối START → find_ffmpeg → lệnh run? Được gọi từ if __name__ == '__main__'. "
        "Function gọi tiếp: run_pipeline.",
    )

    _heading(doc, "Khối: Load config + bắt buộc VMAF", 3)
    _code(
        doc,
        "if not videos:\n"
        "    raise ValueError(\"Chua cung cap video dau vao.\")\n"
        "if not bool(cfg.quality.get(\"vmaf\", False)):\n"
        "    raise RuntimeError(\n"
        "        \"Pipeline hull-based can VMAF that. Bat quality.vmaf trong config; khong dung so lieu gia.\"\n"
        "    )",
        "src/pipeline.py — đầu run_pipeline",
    )
    _para(
        doc,
        "Điều kiện: danh sách video không rỗng; quality.vmaf phải true. YES: tạo thư mục results. "
        "NO: ném exception, không chạy encode, không bịa VMAF.",
    )

    _heading(doc, "Khối: FFprobe + SI/TI", 3)
    _code(
        doc,
        "meta = probe_video(path, tools)\n"
        "if meta.width < 16 or meta.height < 16:\n"
        "    raise ValueError(...)\n"
        "if meta.duration_seconds <= 0.2:\n"
        "    raise ValueError(...)\n"
        "complexity = analyze_complexity(meta, tools, cfg)",
        "src/analyzer/feature_extractor.py — extract_features",
    )
    _para(
        doc,
        "Được gọi từ run_pipeline (và analyze). Output: VideoFeatures (meta, complexity, adjusted_k, adjusted_label). "
        "k chỉ dùng cho build_per_title_ladder, không chọn ladder hull.",
    )

    _heading(doc, "Khối: Candidate generation + không upscale", 3)
    _code(
        doc,
        "for spec in cfg.candidates:\n"
        "    if spec.height > meta.height:\n"
        "        continue\n"
        "    ...\n"
        "    for bitrate in spec.bitrates_kbps:\n"
        "        if bitrate <= 0: raise ValueError(...)\n"
        "        if bitrate in seen: raise ValueError(...)",
        "src/ladder/models.py — build_candidate_rungs",
    )
    _para(
        doc,
        "candidates được tạo từ config.yaml. Mỗi spec một height; mỗi bitrate một LadderRung source='candidate'. "
        "Vòng ngoài: số height trong YAML. Vòng trong: len(bitrates_kbps). Kết thúc khi duyệt hết spec. "
        "Sau lọc nếu rungs rỗng → ValueError (không còn candidate phù hợp).",
    )

    _heading(doc, "Khối: FFmpeg Encode", 3)
    _code(
        doc,
        "cmd = _base_args(tools, source, rung, cfg, meta) + [str(output)]\n"
        "completed = run_ffmpeg(cmd, timeout=600)\n"
        "require_success(completed, f\"encode {rung.name}\")\n"
        "...\n"
        "if not output.is_file() or output.stat().st_size < 100:\n"
        "    raise RuntimeError(f\"File encode khong hop le: {output}\")",
        "src/encoder/ffmpeg_encoder.py — encode_rung (two_pass mặc định false)",
    )
    _para(
        doc,
        "Trong Flowchart: khối FFmpeg Encode. Gọi từ _encode_and_score khi cache miss. "
        "Gọi tiếp: probe_video(output) lấy actual bitrate, rồi measure_quality. "
        "YES (file hợp lệ): trả EncodeResult. NO: RuntimeError. "
        "require_success: returncode != 0 → RuntimeError kèm stderr, không bỏ qua.",
    )

    _heading(doc, "Khối: VMAF", 3)
    _code(
        doc,
        "if cfg.quality.get(\"vmaf\", False):\n"
        "    model = str(cfg.quality.get(\"vmaf_model\", \"version=vmaf_v0.6.1\"))\n"
        "    vmaf_filter = f\"libvmaf=model={model}:n_threads=4\"\n"
        "    text = _run_filter(..., vmaf_filter)\n"
        "    vmaf_val = parse_vmaf_score(text)\n"
        "    if vmaf_val is None:\n"
        "        raise RuntimeError(...)",
        "src/metrics/quality_metrics.py — measure_quality",
    )
    _para(
        doc,
        "Được gọi sau mỗi encode (trừ khi cache hit). Filter scale encoded về đúng width/height nguồn. "
        "Regex VMAF score:. Không invent điểm.",
    )

    _heading(doc, "Khối: vòng lặp candidate + cache", 3)
    _code(
        doc,
        "for rung in candidates:\n"
        "    encoded, quality = _encode_and_score(\n"
        "        video, meta, rung, \"candidate\", candidate_dir, tools, cfg, cache\n"
        "    )\n"
        "    row = row_from(..., method=\"candidate\")\n"
        "    rows.append(row)\n"
        "    candidate_rows.append(row)",
        "src/pipeline.py — vòng candidate",
    )
    _para(
        doc,
        "candidates đến từ build_candidate_rungs. Mỗi vòng: một (height, target bitrate). "
        "Kết thúc khi hết list. Dữ liệu lưu rows (toàn thí nghiệm) và candidate_rows (video hiện tại). "
        "Sau vòng: _rq_point → Pareto.",
    )
    _code(
        doc,
        "key = (rung.height, rung.bitrate_kbps)\n"
        "cached = cache.get(key)\n"
        "if cached is not None:\n"
        "    return cached\n"
        "encoded = encode_rung(...)\n"
        "quality = measure_quality(...)\n"
        "cache[key] = (encoded, quality)",
        "src/pipeline.py — _encode_and_score",
    )
    _para(
        doc,
        "Điều kiện cache: cùng height và bitrate mục tiêu đã encode (ví dụ candidate 360p@365 trùng fixed 360p@365). "
        "HIT: không gọi FFmpeg lại. MISS: encode + đo, ghi cache.",
    )

    _heading(doc, "Khối: Pareto", 3)
    _code(
        doc,
        "bitrate_le = b.bitrate_kbps <= a.bitrate_kbps\n"
        "vmaf_ge = b.vmaf >= a.vmaf\n"
        "strict = (b.bitrate_kbps < a.bitrate_kbps) or (b.vmaf > a.vmaf)\n"
        "if bitrate_le and vmaf_ge and strict:\n"
        "    dominated = True",
        "src/analysis/rq_points.py — remove_dominated_points",
    )
    _para(
        doc,
        "Hai vòng lặp trên tập điểm hữu hạn. Pareto = các điểm không dominated. "
        "Hai điểm trùng bitrate và VMAF: không điểm nào dominate (thiếu strict) → cả hai giữ.",
    )

    _heading(doc, "Khối: Upper Convex Hull", 3)
    _code(
        doc,
        "if len(unique) <= 2:\n"
        "    return unique\n"
        "hull: list[RQPoint] = []\n"
        "for point in unique:\n"
        "    while len(hull) >= 2 and _cross(hull[-2], hull[-1], point) >= 0:\n"
        "        hull.pop()\n"
        "    hull.append(point)",
        "src/analysis/rq_points.py — upper_convex_hull",
    )
    _para(
        doc,
        "Input nên là Pareto (pipeline gọi đúng thứ tự). Trùng bitrate: giữ VMAF cao hơn. "
        "cross >= 0: bỏ điểm làm ngoặt trái hoặc thẳng (collinear giữa).",
    )

    _heading(doc, "Khối: Ladder selection", 3)
    _code(
        doc,
        "best = max(group, key=lambda item: (item.vmaf, -_ladder_bitrate(item)))\n"
        "...\n"
        "bitrate = _ladder_bitrate(point)  # target_bitrate_kbps ưu tiên\n"
        "if bitrate > last_br:\n"
        "    monotonic.append(point)",
        "src/ladder/models.py — select_ladder_from_hull",
    )
    _para(
        doc,
        "Output: list[LadderRung] source='hull'. Gọi tiếp validate_ladder rồi vòng encode 3 phương pháp.",
    )

    _heading(doc, "Khối: Output", 3)
    _code(
        doc,
        "write_csv(csv_path, rows)\n"
        "_write_bitrate_vmaf_csv(vmaf_csv_path, rows)\n"
        "write_json(json_path, payload)\n"
        "plot_files = plot_results(rows, plots_dir, analyses=analyses)",
        "src/pipeline.py — sau vòng for videos",
    )
    _para(
        doc,
        "Chỉ chạy khi đã xử lý hết video. bitrate_vmaf.csv chỉ gồm method=='candidate'. "
        "plot_results vẽ 3 PNG cũ + bitrate_vmaf.png nếu có VMAF.",
    )

    _heading(doc, "4A.7. Điều kiện rẽ nhánh (diamond)", 2)
    _table(
        doc,
        ["Điều kiện", "File / function", "YES", "NO"],
        [
            ["FFmpeg không thấy", "ffmpeg_tools.find_ffmpeg_tools / main", "—", "log, return 2"],
            ["command != run", "main()", "check-env/make-sample/analyze rồi END", "load_config + run_pipeline"],
            ["videos rỗng", "run_pipeline", "ValueError", "tiếp tục"],
            ["quality.vmaf false", "run_pipeline", "RuntimeError (không giả VMAF)", "encode + libvmaf"],
            ["width/height < 16 hoặc duration ≤ 0.2", "extract_features", "ValueError", "analyze_complexity"],
            ["probe.enabled", "extract_features", "CRF probe, có thể đổi nhãn/k", "k = complexity.k (mặc định YAML false)"],
            ["spec.height > meta.height", "build_candidate_rungs", "continue, không upscale", "thêm rung"],
            ["bitrate ≤ 0 hoặc trùng", "build_candidate_rungs", "ValueError", "append LadderRung"],
            ["rungs rỗng sau lọc", "build_candidate_rungs", "ValueError", "trả list candidate"],
            ["cache hit", "_encode_and_score", "return EncodeResult cũ", "encode_rung + measure_quality"],
            ["two_pass", "encode_rung", "pass 1 NUL + pass 2 file", "một pass (mặc định)"],
            ["FFmpeg exit ≠ 0", "require_success", "RuntimeError + stderr", "tiếp tục"],
            ["file encode < 100 byte", "encode_rung", "RuntimeError", "probe bitrate thực"],
            ["Không parse PSNR/SSIM/VMAF", "measure_quality", "RuntimeError", "gán QualityScores"],
            ["B dominate A", "remove_dominated_points", "bỏ A khỏi Pareto", "giữ A"],
            ["len(unique) ≤ 2", "upper_convex_hull", "return unique", "monotone chain"],
            ["hull rỗng", "select_ladder_from_hull", "ValueError", "lọc min_vmaf"],
            ["prefer_one_per_height", "select_ladder_from_hull", "1 điểm/height", "sort theo bitrate"],
            ["target bitrate không tăng", "select_ladder_from_hull", "bỏ điểm", "append monotonic"],
            ["len > max_representations", "select_ladder_from_hull", "subsample", "giữ hết monotonic"],
        ],
        "Bảng F.2. Mọi diamond quan trọng khớp điều kiện trong code",
    )

    _heading(doc, "4A.8. Vòng lặp", 2)
    _para(
        doc,
        "Vòng 1 — for raw in videos (pipeline.py): mỗi file đầu vào một lần. videos do CLI nargs='+'. "
        "Kết thúc hết danh sách. Sau vòng: ghi CSV/JSON/plot cho cả thí nghiệm.",
    )
    _para(
        doc,
        "Vòng 2 — for spec in cfg.candidates rồi for bitrate in spec.bitrates_kbps (build_candidate_rungs): "
        "số phần tử phụ thuộc YAML và chiều cao nguồn. Nguồn 720p bỏ spec 1080. "
        "Mỗi vòng trong tạo một LadderRung.",
    )
    _para(
        doc,
        "Vòng 3 — for rung in candidates: encode + VMAF. Dữ liệu append vào rows và candidate_rows. "
        "Số lần = len(candidates) (12 với clip 720p lần thí nghiệm).",
    )
    _para(
        doc,
        "Vòng 4 — for a in valid / for b in valid (remove_dominated_points): so từng cặp. "
        "Kết thúc hết điểm hữu hạn.",
    )
    _para(
        doc,
        "Vòng 5 — for point in unique (upper_convex_hull): while pop khi cross>=0. "
        "Kết thúc hết điểm unique theo bitrate.",
    )
    _para(
        doc,
        "Vòng 6 — for method, ladder, method_dir in ladders rồi for rung in ladder: encode hull/fixed/per_title "
        "với cache. ladders luôn 3 phương pháp. Số rung từng ladder do selection/fixed/k quyết định.",
    )

    _heading(doc, "4A.9. Luồng dữ liệu (data flow)", 2)
    _code(
        doc,
        "Path video\n"
        "  → VideoMeta          (probe_video)\n"
        "  → ComplexityResult   (analyze_complexity) + adjusted_k\n"
        "  → VideoFeatures      (extract_features)\n"
        "  → list[LadderRung]   (build_candidate_rungs)\n"
        "  → EncodeResult       (encode_rung)\n"
        "  → QualityScores      (measure_quality)\n"
        "  → ExperimentRow      (row_from)\n"
        "  → RQPoint            (_rq_point)\n"
        "  → Pareto list[RQPoint]\n"
        "  → Hull list[RQPoint]\n"
        "  → list[LadderRung] source=hull / fixed / per_title\n"
        "  → CSV / JSON / PNG",
        "Data flow thực tế — tên kiểu lấy từ dataclass trong code",
    )
    _table(
        doc,
        ["Kiểu", "Tạo tại", "Trường chính", "Ai dùng", "Ghi ra"],
        [
            ["VideoMeta", "probe_video", "width, height, fps, duration, codec, bitrate_bps", "complexity, ladder, encoder, metrics", "analyses JSON"],
            ["ComplexityResult", "analyze_complexity", "si, ti, index, label, k", "feature_extractor, row_from", "analyses + CSV k/label"],
            ["AppConfig", "load_config", "fixed_ladder, candidates, quality, ladder_selection", "mọi bước", "—"],
            ["LadderRung", "build_* / select_*", "name, width, height, bitrate_kbps, source", "encode_rung", "analyses ladders"],
            ["EncodeResult", "encode_rung", "output, actual_bitrate_kbps, size_bytes, elapsed", "row_from", "output_file CSV"],
            ["QualityScores", "measure_quality", "psnr_average, ssim_all, vmaf, notes", "row_from", "cột psnr/ssim/vmaf"],
            ["ExperimentRow", "row_from", "method, rung, target/actual, metrics", "CSV, plot, _rq_point", "experiment_results.csv"],
            ["RQPoint", "_rq_point / RQPoint", "bitrate_kbps, vmaf, height, target_...", "Pareto, hull, select", "JSON rq_points/pareto/convex_hull"],
        ],
        "Bảng F.3. Data flow — kiểu dữ liệu thực tế",
    )

    _heading(doc, "4A.10. Vì sao thứ tự các khối như vậy", 2)
    _para(doc, "FFprobe trước SI/TI: analyze_complexity cần width/height/fps/path.")
    _para(doc, "SI/TI trước encode: không bắt buộc cho hull, nhưng pipeline lấy k cho heuristic cùng lúc với metadata, trước khi tốn thời gian encode.")
    _para(doc, "Candidate trước VMAF: không có file encode thì không có điểm đo.")
    _para(doc, "VMAF trước Pareto: domination dùng bitrate thực và VMAF; thiếu VMAF thì _rq_point raise.")
    _para(doc, "Pareto trước hull: hull là envelope của tập không dominated; pipeline gọi đúng thứ tự này.")
    _para(doc, "Hull trước select_ladder_from_hull: hàm nhận list[RQPoint] hull, không nhận toàn bộ candidate.")
    _para(doc, "Fixed/heuristic encode sau hull: cùng metric để so sánh; cache tránh encode lại điểm trùng.")
    _para(doc, "Ghi file sau hết video: một CSV/JSON cho cả thí nghiệm, không ghi giữa chừng.")

    _heading(doc, "4A.11. Cách trình bày Flowchart khi bảo vệ (3–5 phút)", 2)
    _para(
        doc,
        "1. Input: một hoặc nhiều file video, cộng config.yaml. Chương trình bắt đầu từ main() trong src/main.py, "
        "không phải từ SI/TI.",
    )
    _para(
        doc,
        "2. Tìm FFmpeg; lệnh run thì load_config rồi run_pipeline. Metadata lấy bằng probe_video (FFprobe JSON).",
    )
    _para(
        doc,
        "3. SI/TI trong analyze_complexity: mô tả độ phức tạp, giải thích khác biệt đường cong; k chỉ nhân ladder heuristic.",
    )
    _para(
        doc,
        "4. Candidate: build_candidate_rungs đọc YAML, bỏ height > nguồn. Vòng for rung in candidates gọi _encode_and_score.",
    )
    _para(
        doc,
        "5. VMAF: measure_quality → libvmaf model version=vmaf_v0.6.1, parse VMAF score. PSNR/SSIM phụ.",
    )
    _para(
        doc,
        "6. Dataset: mỗi candidate một ExperimentRow / RQPoint. Loại dominated bằng remove_dominated_points = Pareto. "
        "Upper hull monotone chain, khác Pareto.",
    )
    _para(
        doc,
        "7. Per-Title chính: select_ladder_from_hull (không lấy hết hull). Fixed ladder là baseline Apple. "
        "Heuristic k×fixed vẫn encode để so. Output: CSV, bitrate_vmaf.csv, JSON, PNG, mp4.",
    )

    _heading(doc, "4A.12. Câu hỏi bảo vệ dựa trên Flowchart và source code", 2)
    qa = [
        ("Chương trình bắt đầu từ đâu?",
         "Hàm main() trong src/main.py, gọi từ if __name__ == '__main__'. Không bắt đầu từ pipeline."),
        ("Input là gì?",
         "args.videos: list[Path] từ CLI. Config mặc định config/config.yaml. Output dir args.output (results)."),
        ("Khối find_ffmpeg_tools làm gì?",
         "Tìm ffmpeg.exe/ffprobe (PATH, FFMPEG_BIN, WinGet Gyan). Không thấy: FFmpegNotFoundError, main return 2."),
        ("Vì sao FFprobe đứng trước encode?",
         "Cần width/height để không upscale, tính size_for_height, GOP, và scale metric về độ phân giải nguồn."),
        ("Lệnh analyze khác run thế nào?",
         "analyze: extract_features + in JSON ladder, không encode, không VMAF. run: run_pipeline đầy đủ."),
        ("Vòng for raw in videos kết thúc khi nào?",
         "Khi hết danh sách Path. Mỗi phần tử require_file rồi xử lý một video."),
        ("candidates được tạo ở đâu, có bao nhiêu?",
         "build_candidate_rungs(meta, cfg). Số lượng = tổng bitrate các height ≤ nguồn. Clip 720p lần chạy: 12."),
        ("spec.height > meta.height thì sao?",
         "continue; không tạo rung. Nguồn 720p bỏ candidate 1080p. Nếu sau lọc rỗng: ValueError."),
        ("Vòng for rung in candidates xử lý gì, lưu đâu?",
         "Một LadderRung: encode + quality + row_from. Append rows và candidate_rows."),
        ("Cache hoạt động thế nào?",
         "_encode_and_score key=(height, bitrate_kbps). Trùng thì không gọi FFmpeg/VMAF lại."),
        ("FFmpeg lỗi thì sao?",
         "run_ffmpeg không check=True; require_success thấy returncode!=0 thì RuntimeError. Encode dừng."),
        ("File encode không hợp lệ?",
         "encode_rung: không tồn tại hoặc size<100 → RuntimeError."),
        ("VMAF không chạy / không parse?",
         "quality.vmaf false: RuntimeError ngay đầu pipeline. Parse None: RuntimeError trong measure_quality. Test integration skip nếu không có libvmaf, không biến fail thành pass."),
        ("PSNR/SSIM nằm khối nào?",
         "Cùng measure_quality, trước/cùng VMAF theo cờ YAML; metric phụ, không chọn hull."),
        ("_rq_point trả về gì?",
         "RQPoint; nếu row.vmaf is None thì RuntimeError."),
        ("Dominated point là gì? File nào?",
         "rq_points.py remove_dominated_points: B dominate A khi B rẻ hơn hoặc bằng và VMAF tốt hơn hoặc bằng, có strict."),
        ("Pareto Frontier là gì trong code?",
         "pareto_frontier = remove_dominated_points. Không phải hull."),
        ("Convex hull khác Pareto thế nào?",
         "Pareto: không dominated. Hull: monotone chain upper envelope, có thể bỏ điểm Pareto lõm. Pipeline: Pareto rồi hull."),
        ("Hai điểm cùng bitrate thì sao?",
         "Pareto: VMAF thấp hơn bị dominate. Hull: dict theo bitrate giữ VMAF cao nhất."),
        ("Ladder chọn từ hull thế nào?",
         "select_ladder_from_hull: min_vmaf; một height một điểm VMAF max; target bitrate tăng; cắt max_representations. Không phải tối ưu toàn cục."),
        ("Vì sao monotonic dùng target không dùng actual?",
         "_ladder_bitrate: target_bitrate_kbps. smptebars actual ~20 kbps mọi bậc — nếu dùng actual thì mất hết resolution."),
        ("Fixed ladder dùng làm gì trên Flowchart?",
         "Baseline độc lập nội dung, encode sau khi đã có hull, cùng VMAF/PSNR/SSIM để so."),
        ("Heuristic k×fixed nằm khối nào?",
         "build_per_title_ladder; method='per_title'. Không xóa, không phải hull."),
        ("Sau run_pipeline dữ liệu đi đâu?",
         "return dict summary; main in JSON. File: CSV, bitrate_vmaf.csv, JSON, plots, encodes."),
        ("Word report có trong Flowchart run không?",
         "Không. tools/build_report.py / build_code_explanation.py là lệnh riêng sau thí nghiệm."),
        ("Function nào vẽ bitrate_vmaf.png?",
         "visualization/plots.py plot_results → _plot_bitrate_vmaf. Candidate, Pareto, hull, selected."),
        ("validate_ladder kiểm tra gì?",
         "Ladder rỗng; kích thước chẵn; không upscale; bitrate trong min/max; bitrate tăng dần."),
        ("Nếu hull rỗng / monotonic rỗng?",
         "select_ladder_from_hull raise ValueError. Không bịa ladder."),
        ("Biến nào nối encode và Pareto?",
         "candidate_rows: list[ExperimentRow] → list[RQPoint] qua _rq_point."),
        ("Tại sao đo quality scale về độ phân giải nguồn?",
         "_run_filter scale encoded về source_meta.width/height rồi psnr/ssim/libvmaf — để so 360p với 720p cùng một reference."),
    ]
    for i, (q, a) in enumerate(qa, start=1):
        _heading(doc, f"Câu F.{i}. {q}", 3)
        _para(doc, a)

    _note(
        doc,
        "Nhắc khi bảo vệ",
        "Chỉ vào khối trên Hình F.1–F.4 rồi mở đúng file/function trong bảng F.1. "
        "Không gọi Pareto là Convex Hull. Không gọi hull-based selection là tối ưu toàn cục. "
        "Không nói SI/TI đang gán bitrate cho phương pháp chính.",
    )


def _move_before(marker, elements: list) -> None:
    """Insert elements (already in desired order) immediately before marker."""
    for el in elements:
        marker.addprevious(el)


def repair_chapter_order(doc: Document) -> None:
    """Put chapter 4A in reading order after chapter 4, then heading 5."""
    h4 = h4a = h5 = hinh41 = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if text.startswith("4. Luồng xử lý dữ liệu"):
            h4 = para._element
        elif text.startswith("Hình 4.1"):
            hinh41 = para._element
        elif text.startswith("4A. FLOWCHART"):
            h4a = para._element
        elif text == MARKER:
            h5 = para._element
    if hinh41 is None or h4a is None or h5 is None:
        raise RuntimeError("Thieu neo Hinh 4.1 / 4A / heading 5.")
    nodes = []
    el = hinh41.getnext()
    while el is not None and el is not h5 and not str(el.tag).endswith("sectPr"):
        nodes.append(el)
        el = el.getnext()
    if not nodes:
        return
    parent = h5.getparent()
    for node in nodes:
        parent.remove(node)
    desired = list(reversed(nodes))
    for node in desired:
        h5.addprevious(node)


def insert_into_existing() -> Path:
    if not DOCX.is_file():
        raise FileNotFoundError(DOCX)
    drawn = draw_all()
    by_name = {
        "main": drawn[0],
        "candidate": drawn[1],
        "pareto": drawn[2],
        "ladder": drawn[3],
    }
    doc = Document(str(DOCX))
    already = any(p.text.strip().startswith("4A. FLOWCHART") for p in doc.paragraphs)
    if already:
        texts = [p.text.strip() for p in doc.paragraphs]
        try:
            i41 = next(i for i, t in enumerate(texts) if t.startswith("Hình 4.1"))
            i4a = next(i for i, t in enumerate(texts) if t.startswith("4A. FLOWCHART"))
            i5 = next(i for i, t in enumerate(texts) if t == MARKER)
        except StopIteration:
            i41 = i4a = i5 = -1
        if i41 != -1 and i4a == i41 + 1 and i5 > i4a:
            return DOCX
        repair_chapter_order(doc)
        doc.save(str(DOCX))
        return DOCX

    marker = None
    for para in doc.paragraphs:
        if para.text.strip() == MARKER:
            marker = para._element
            break
    if marker is None:
        raise RuntimeError(f"Khong tim thay heading {MARKER!r} trong DOCX hien co.")
    body = doc.element.body
    n_before = len(list(body))
    add_flowchart_chapter(doc, by_name)
    after = list(body)
    if str(after[-1].tag).endswith("sectPr"):
        new_els = after[n_before - 1 : -1]
    else:
        new_els = after[n_before:]
    _move_before(marker, new_els)
    doc.save(str(DOCX))
    return DOCX


if __name__ == "__main__":
    print(insert_into_existing())
