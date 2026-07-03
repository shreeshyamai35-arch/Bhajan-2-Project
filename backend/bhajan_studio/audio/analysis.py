"""Vocal analysis: duration, loudness, leading-silence offset, tempo, key.

librosa is used when available for BPM / key estimation. If it is not
installed, we fall back to the BPM / key supplied in the BhajanSpec so the
pipeline still runs.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..config import NOTE_FREQS, SAMPLE_RATE


@dataclass
class VocalAnalysis:
    duration_s: float
    rms: float
    lead_silence_s: float
    detected_bpm: float | None
    detected_key: str | None
    used_librosa: bool


def analyze_vocal(mono: np.ndarray, fallback_bpm: float, fallback_key: str,
                  sr: int = SAMPLE_RATE) -> VocalAnalysis:
    duration = mono.size / sr if mono.size else 0.0
    rms = float(np.sqrt(np.mean(mono ** 2))) if mono.size else 0.0
    lead = _leading_silence_seconds(mono, sr)

    bpm: float | None = None
    key: str | None = None
    used = False
    try:
        import librosa  # type: ignore

        used = True
        if mono.size > sr:  # need at least ~1s
            tempo, _ = librosa.beat.beat_track(y=mono, sr=sr)
            bpm = float(np.atleast_1d(tempo)[0])
            key = _estimate_key_librosa(mono, sr)
    except Exception:
        used = False

    return VocalAnalysis(
        duration_s=duration,
        rms=rms,
        lead_silence_s=lead,
        detected_bpm=bpm if bpm else fallback_bpm,
        detected_key=key if key else fallback_key,
        used_librosa=used,
    )


def _leading_silence_seconds(mono: np.ndarray, sr: int, thresh: float = 0.01) -> float:
    if mono.size == 0:
        return 0.0
    above = np.abs(mono) > thresh
    idx = np.argmax(above)
    if not above.any():
        return 0.0
    return idx / sr


def _estimate_key_librosa(mono: np.ndarray, sr: int) -> str:
    import librosa  # type: ignore

    chroma = librosa.feature.chroma_cqt(y=mono, sr=sr)
    profile = chroma.mean(axis=1)
    pitch_classes = ["C", "C#", "D", "D#", "E", "F",
                     "F#", "G", "G#", "A", "A#", "B"]
    best = pitch_classes[int(np.argmax(profile))]
    return best if best in NOTE_FREQS else "C"
