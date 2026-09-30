from pathlib import Path

from metrics.result_collector import ExperimentRow, write_csv, write_json
from visualization.plots import plot_results


def _row(method: str, rung: str, bitrate: int, size: int, ssim: float) -> ExperimentRow:
    return ExperimentRow(
        video="clip.mp4",
        method=method,
        rung=rung,
        width=640,
        height=360,
        target_bitrate_kbps=bitrate,
        actual_bitrate_kbps=float(bitrate),
        size_bytes=size,
        encode_seconds=1.0,
        psnr=35.0,
        ssim=ssim,
        vmaf=None,
        vmaf_min=None,
        vmaf_max=None,
        complexity_label="medium",
        complexity_index=0.5,
        k=1.0,
        output_file="out.mp4",
    )


def test_csv_json_export(tmp_path):
    rows = [
        _row("fixed", "360p", 365, 80_000, 0.90),
        _row("per_title", "360p", 250, 60_000, 0.88),
    ]
    csv_path = tmp_path / "out.csv"
    json_path = tmp_path / "out.json"
    write_csv(csv_path, rows)
    write_json(json_path, {"rows": 2})
    text = csv_path.read_text(encoding="utf-8")
    assert "per_title" in text
    assert json_path.read_text(encoding="utf-8").strip().startswith("{")


def test_plots_created(tmp_path):
    rows = [
        _row("fixed", "360p", 365, 80_000, 0.90),
        _row("fixed", "432p", 730, 140_000, 0.93),
        _row("per_title", "360p", 250, 60_000, 0.88),
        _row("per_title", "432p", 500, 100_000, 0.91),
    ]
    created = plot_results(rows, tmp_path)
    assert created
    assert all(Path(path).is_file() for path in created)
