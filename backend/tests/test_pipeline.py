"""End-to-end and unit tests for the Phase 1 pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bhajan_studio.audio import master  # noqa: E402
from bhajan_studio.audio.io import load_mono, save_wav, to_stereo  # noqa: E402
from bhajan_studio.config import TARGET_LUFS, BhajanSpec  # noqa: E402
from bhajan_studio.orchestrator import produce_bhajan  # noqa: E402
from bhajan_studio.prompts.phonetics import correct_pronunciation  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from make_sample_vocal import make_sample_vocal  # noqa: E402


def test_phonetic_correction():
    text = "Jai Shyam Radhe Govind, Krishna Murari"
    corrected, changes = correct_pronunciation(text)
    assert "Shyaam" in corrected
    assert "Raa-dhe" in corrected
    assert any("Shyam -> Shyaam" in c for c in changes)


def test_master_hits_target_lufs():
    # 3s of pink-ish noise, master it, expect ~ -14 LUFS.
    rng = np.random.default_rng(1)
    mono = (rng.standard_normal(44100 * 3) * 0.1).astype(np.float32)
    res = master.master(to_stereo(mono))
    assert abs(res.output_lufs - TARGET_LUFS) <= 1.0
    assert res.peak_dbfs <= -0.9


def test_end_to_end_pipeline(tmp_path):
    vocal = make_sample_vocal(seconds=10.0, key="C")
    vocal_path = tmp_path / "vocal.wav"
    save_wav(vocal_path, vocal)

    spec = BhajanSpec(
        lyrics="Jai Shyam, Radhe Govind",
        bpm=90, key="C", taal="keherwa", title="Test Bhajan",
    )
    result = produce_bhajan(vocal_path, spec, tmp_path / "out", seed=7)

    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.passed, result.qc.summary()

    # Output should be a real stereo file at the vocal length (~10s).
    out = load_mono(result.output_path)
    assert 9.0 <= out.size / 44100 <= 11.0
    assert result.instrumental_source in {"mock", "lyria"}
