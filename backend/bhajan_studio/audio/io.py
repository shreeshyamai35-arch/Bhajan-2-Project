"""WAV load/save helpers. Internal audio is float32 in [-1, 1].

We keep processing simple and dependency-light: mono float arrays for DSP,
stereo only at the final master. Uses soundfile (libsndfile) for WAV I/O so
no external ffmpeg is required for the core pipeline.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from ..config import SAMPLE_RATE


def load_mono(path: str | Path, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Load an audio file as mono float32 at target_sr (naive resample)."""
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr != target_sr:
        mono = _resample_linear(mono, sr, target_sr)
    return mono.astype(np.float32)


def _resample_linear(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out or x.size == 0:
        return x
    n_out = int(round(x.size * sr_out / sr_in))
    src_idx = np.linspace(0, x.size - 1, num=n_out)
    return np.interp(src_idx, np.arange(x.size), x).astype(np.float32)


def save_wav(path: str | Path, audio: np.ndarray, sr: int = SAMPLE_RATE) -> Path:
    """Save mono or stereo float audio to a 16-bit-safe WAV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(audio, dtype=np.float32)
    arr = np.clip(arr, -1.0, 1.0)
    sf.write(str(path), arr.T if arr.ndim == 2 else arr, sr, subtype="PCM_16")
    return path


def to_stereo(mono: np.ndarray) -> np.ndarray:
    """Duplicate a mono signal to a (2, N) stereo array."""
    mono = np.asarray(mono, dtype=np.float32)
    return np.stack([mono, mono], axis=0)


def peak_dbfs(audio: np.ndarray) -> float:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak <= 0:
        return -np.inf
    return 20.0 * np.log10(peak)
