"""Mastering: normalise to -14 LUFS and cap true peak at -1 dBFS.

Uses pyloudnorm for ITU-R BS.1770 integrated loudness. After loudness
normalisation we apply a hard ceiling so the file never clips.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyloudnorm as pyln

from ..config import (SAMPLE_RATE, TARGET_LUFS, TARGET_TRUE_PEAK_DBFS)


@dataclass
class MasterResult:
    audio: np.ndarray          # stereo (2, N)
    input_lufs: float
    output_lufs: float
    peak_dbfs: float


def master(stereo: np.ndarray, sr: int = SAMPLE_RATE,
           target_lufs: float = TARGET_LUFS) -> MasterResult:
    # pyloudnorm expects (samples, channels)
    interleaved = stereo.T.astype(np.float64)

    meter = pyln.Meter(sr)
    in_lufs = float(meter.integrated_loudness(interleaved))

    if np.isinf(in_lufs) or np.isnan(in_lufs):
        # Effectively silent input; return unchanged.
        return MasterResult(stereo, in_lufs, in_lufs, _peak_dbfs(stereo))

    normalized = pyln.normalize.loudness(interleaved, in_lufs, target_lufs)
    normalized = _ceiling(normalized, TARGET_TRUE_PEAK_DBFS)

    out = normalized.T.astype(np.float32)
    out_lufs = float(meter.integrated_loudness(normalized))
    return MasterResult(out, in_lufs, out_lufs, _peak_dbfs(out))


def _ceiling(x: np.ndarray, ceiling_dbfs: float) -> np.ndarray:
    ceiling = 10.0 ** (ceiling_dbfs / 20.0)
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > ceiling and peak > 0:
        x = x * (ceiling / peak)
    return x


def _peak_dbfs(x: np.ndarray) -> float:
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak <= 0:
        return float("-inf")
    return 20.0 * np.log10(peak)
