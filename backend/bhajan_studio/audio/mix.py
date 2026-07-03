"""Mix the aligned vocal + instrumental into a stereo bus.

Devotional mixing rule: the lead vocal sits clearly on TOP. The instrumental
is attenuated to make room, and a light reverb adds a temple/hall sense of
space without drowning the voice.
"""
from __future__ import annotations

import numpy as np

from ..config import SAMPLE_RATE
from .io import to_stereo


def mix(
    vocal: np.ndarray,
    instrumental: np.ndarray,
    vocal_gain_db: float = 0.0,
    instrumental_gain_db: float = -6.0,
    reverb_amount: float = 0.18,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Return a stereo (2, N) float mix, pre-master (leaves headroom)."""
    v = vocal * _db_to_lin(vocal_gain_db)
    i = instrumental * _db_to_lin(instrumental_gain_db)

    wet_v = _simple_reverb(v, sr, amount=reverb_amount)
    bus = wet_v + i

    # Leave headroom for the mastering stage.
    peak = float(np.max(np.abs(bus))) or 1.0
    if peak > 0.89:
        bus = bus / peak * 0.89

    return to_stereo(bus.astype(np.float32))


def _db_to_lin(db: float) -> float:
    return float(10.0 ** (db / 20.0))


def _simple_reverb(x: np.ndarray, sr: int, amount: float) -> np.ndarray:
    """Lightweight multi-tap decaying reverb (no scipy dependency)."""
    if amount <= 0 or x.size == 0:
        return x
    taps_ms = [23, 41, 67, 97, 131]
    decays = [0.7, 0.55, 0.42, 0.31, 0.22]
    wet = np.zeros_like(x)
    for ms, d in zip(taps_ms, decays):
        delay = int(sr * ms / 1000.0)
        if delay >= x.size:
            continue
        wet[delay:] += d * x[:-delay]
    return (x + amount * wet).astype(np.float32)
