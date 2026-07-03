"""Align the real vocal with the generated instrumental.

For the vocal-first workflow the singer records to a fixed click at a known
BPM, and the instrumental is generated at that same BPM, so alignment is
mostly about matching lengths and start offsets. We trim/pad the instrumental
to the vocal length and keep both starting together.
"""
from __future__ import annotations

import numpy as np


def fit_length(signal: np.ndarray, target_len: int) -> np.ndarray:
    """Trim or zero-pad `signal` to exactly target_len samples."""
    if signal.size == target_len:
        return signal.astype(np.float32)
    if signal.size > target_len:
        return signal[:target_len].astype(np.float32)
    out = np.zeros(target_len, dtype=np.float32)
    out[: signal.size] = signal
    return out


def align_vocal_and_instrumental(
    vocal: np.ndarray, instrumental: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return (vocal, instrumental) at a common length.

    The common length is the vocal length: the finished song is as long as the
    sung performance, with the instrumental fitted to it.
    """
    target = vocal.size
    return vocal.astype(np.float32), fit_length(instrumental, target)
