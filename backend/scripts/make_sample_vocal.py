"""Generate a synthetic 'sung' vocal WAV for testing the pipeline offline.

This is NOT a real voice - it is a simple vowel-like tone following a short
melody, just so the end-to-end pipeline has realistic input to process when no
recorded vocal is available. Real usage takes an actual recording.

Usage: python scripts/make_sample_vocal.py sample_vocal.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Allow running as a plain script (add backend/ to path).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bhajan_studio.audio.io import save_wav  # noqa: E402
from bhajan_studio.config import NOTE_FREQS, SAMPLE_RATE  # noqa: E402


def make_sample_vocal(seconds: float = 12.0, key: str = "C") -> np.ndarray:
    sr = SAMPLE_RATE
    tonic = NOTE_FREQS.get(key, 261.63)
    # A simple devotional-ish phrase (scale degrees) in the chosen key.
    ratios = [1.0, 9 / 8, 5 / 4, 4 / 3, 3 / 2, 4 / 3, 5 / 4, 1.0]
    note_len = seconds / len(ratios)
    out = np.zeros(int(seconds * sr), dtype=np.float32)

    for i, r in enumerate(ratios):
        start = int(i * note_len * sr)
        n = int(note_len * sr)
        tt = np.arange(n) / sr
        f = tonic * r
        # Vowel-like tone: fundamental + a couple of formant-ish harmonics.
        tone = (
            0.6 * np.sin(2 * np.pi * f * tt)
            + 0.25 * np.sin(2 * np.pi * 2 * f * tt)
            + 0.12 * np.sin(2 * np.pi * 3 * f * tt)
        )
        # Gentle vibrato + AD envelope.
        tone *= 1.0 + 0.02 * np.sin(2 * np.pi * 5.5 * tt)
        env = np.minimum(1.0, tt / 0.08) * np.exp(-tt * 0.6)
        seg = (tone * env).astype(np.float32)
        end = min(out.size, start + n)
        out[start:end] += seg[: end - start]

    peak = float(np.max(np.abs(out))) or 1.0
    return (out / peak * 0.5).astype(np.float32)


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sample_vocal.wav")
    audio = make_sample_vocal()
    save_wav(dest, audio)
    print(f"wrote sample vocal: {dest} ({audio.size / SAMPLE_RATE:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
