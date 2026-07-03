"""Central configuration and constants for the pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field

# Audio engine constants
SAMPLE_RATE = 44_100          # 44.1 kHz, matches Lyria output
CHANNELS = 2                  # stereo master

# Mastering targets (streaming standard)
TARGET_LUFS = -14.0           # integrated loudness target
TARGET_TRUE_PEAK_DBFS = -1.0  # ceiling to avoid clipping / inter-sample peaks

# QC tolerances
LUFS_TOLERANCE = 1.0          # +/- around TARGET_LUFS
MAX_PEAK_DBFS = -0.9          # anything above this fails QC (clipping risk)
MIN_ACTIVE_RATIO = 0.30       # at least this fraction must be non-silent


# Common Western note -> frequency (Hz) at octave 3/4, used for the mock
# instrument synth and as a fallback tonic reference.
NOTE_FREQS = {
    "C": 261.63, "C#": 277.18, "Db": 277.18, "D": 293.66,
    "D#": 311.13, "Eb": 311.13, "E": 329.63, "F": 349.23,
    "F#": 369.99, "Gb": 369.99, "G": 392.00, "G#": 415.30,
    "Ab": 415.30, "A": 440.00, "A#": 466.16, "Bb": 466.16, "B": 493.88,
}

# Beats-per-bar for common devotional taals.
TAAL_BEATS = {
    "keherwa": 8,
    "dadra": 6,
    "bhajani": 8,
}


@dataclass
class BhajanSpec:
    """Everything needed to produce one bhajan."""

    lyrics: str = ""
    dialect: str = "hindi"            # hindi | braj | rajasthani
    bpm: float = 90.0
    key: str = "C"                    # tonic (Sa)
    taal: str = "keherwa"
    title: str = "Untitled Bhajan"
    instruments: list[str] = field(
        default_factory=lambda: [
            "harmonium", "tabla", "dholak", "bansuri flute", "tanpura drone",
        ]
    )
