# Per-Title Bitrate Ladder Selection cho VOD

Công cụ Python + FFmpeg để **lựa chọn bitrate ladder theo từng nội dung** ở mức thử nghiệm, rồi so sánh với:

1. **Fixed ladder** (baseline độc lập nội dung)
2. **Heuristic per-title** (`k ×` fixed, giữ để đối chiếu)
3. **Hull-based per-title** (phương pháp chính: candidate → VMAF → Pareto → upper convex hull → chọn ladder)

Đây không phải hệ thống tối ưu thương mại kiểu Netflix. Pareto frontier không đồng nghĩa với convex hull. Kết quả chọn ladder được gọi là *hull-based selection*, không phải tối ưu toàn cục.

## Cần cài đặt

- Python 3.11+ (đã kiểm thử 3.12)
- FFmpeg và FFprobe có `libx264` **và `libvmaf`** (bản Gyan full build trên Windows)

Trên Windows:

```text
winget install --id Python.Python.3.12 -e
winget install --id Gyan.FFmpeg -e
```

Mở lại terminal để PATH nhận FFmpeg.

## Cài đặt dự án

```text
cd per-title-encoding
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Kiểm tra môi trường:

```text
python src\main.py check-env
```

## Tạo video mẫu

```text
python src\main.py make-sample --output data\samples\testsrc_720p.mp4 --seconds 4 --size 1280x720 --pattern testsrc
python src\main.py make-sample --output data\samples\smptebars_720p.mp4 --seconds 4 --size 1280x720 --pattern smptebars
python src\main.py make-sample --output data\samples\testsrc2_720p.mp4 --seconds 4 --size 1280x720 --pattern testsrc2
```

## Chạy pipeline

```text
python src\main.py analyze data\samples\testsrc_720p.mp4
python src\main.py run data\samples\testsrc_720p.mp4 data\samples\smptebars_720p.mp4 data\samples\testsrc2_720p.mp4 --output results
```

Kết quả trong `results/`: `experiment_results.csv`, `experiment_results.json`, `bitrate_vmaf.csv`, file encode, biểu đồ PNG (gồm `bitrate_vmaf.png`).

Tạo lại báo cáo Word từ số liệu vừa đo:

```text
python tools\build_report.py
python tools\build_code_explanation.py
```

## Kiểm thử

```text
python -m pytest -q
```

## Pipeline (thực tế)

```text
Video
  → FFprobe
  → SI/TI (mô tả độ phức tạp; k chỉ dùng heuristic baseline)
  → Candidate encoding grid (YAML, không upscale)
  → FFmpeg encode
  → VMAF (metric chính) + PSNR/SSIM (phụ)
  → Bitrate–VMAF dataset
  → Remove dominated points
  → Pareto frontier
  → Upper convex hull
  → Hull-based Per-Title Ladder Selection
  → Fixed ladder + heuristic k×fixed
  → Compare
```

VMAF dùng model built-in `version=vmaf_v0.6.1` qua filter `libvmaf`. Không giả lập điểm VMAF.

## Giới hạn

Không HLS/DASH, không per-shot, không Dynamic Optimizer, không BD-Rate. Không gọi kết quả là tối ưu toàn cục.
