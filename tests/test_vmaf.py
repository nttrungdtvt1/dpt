from encoder.ffmpeg_encoder import encode_rung
from analyzer.video_probe import probe_video
from ladder.models import LadderRung
from metrics.quality_metrics import ffmpeg_has_libvmaf, measure_quality, parse_vmaf_score

import pytest


def test_parse_vmaf_score_typical_ffmpeg_line():
    text = "[Parsed_libvmaf_2] VMAF score: 97.347937\n"
    assert parse_vmaf_score(text) == pytest.approx(97.347937)


def test_parse_vmaf_score_missing():
    assert parse_vmaf_score("nframes: 30 average:41.2") is None
    assert parse_vmaf_score("") is None


def test_real_vmaf_score(sample_video, ffmpeg_tools, test_cfg, tmp_path):
    if not ffmpeg_has_libvmaf(ffmpeg_tools):
        pytest.skip("FFmpeg khong co libvmaf; khong gia lap VMAF.")
    if not test_cfg.quality.get("vmaf"):
        pytest.skip("quality.vmaf tat trong test config.")
    meta = probe_video(sample_video, ffmpeg_tools)
    rung = LadderRung("360p_300k", 640, 360, 300, "candidate")
    encoded = encode_rung(sample_video, meta, rung, "candidate", tmp_path, ffmpeg_tools, test_cfg)
    quality = measure_quality(encoded.output, sample_video, meta, ffmpeg_tools, test_cfg)
    assert quality.vmaf is not None
    assert 0.0 <= quality.vmaf <= 100.0
    assert quality.psnr_average is not None
    assert quality.ssim_all is not None
