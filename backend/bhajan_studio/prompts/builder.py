"""Build the Lyria 3 Pro *instrumental-only* prompt from a BhajanSpec.

Lyria generates its own vocals, so we always request INSTRUMENTAL ONLY and
layer the singer's real vocal ourselves. The prompt encodes the devotional
style, taal, tempo and key so the backing lines up with the recorded vocal.
"""
from __future__ import annotations

from ..config import BhajanSpec


def build_instrumental_prompt(spec: BhajanSpec, duration_seconds: float) -> str:
    instruments = ", ".join(spec.instruments)
    dur = max(15, round(duration_seconds))
    return (
        f"Instrumental only, no vocals, no singing, no choir. "
        f"Traditional Hindi devotional bhajan backing track, temple / satsang "
        f"atmosphere, serene and emotional. Instruments: {instruments}. "
        f"{spec.taal.title()} taal feel, around {spec.bpm:.0f} BPM, "
        f"in the key of {spec.key}. Warm acoustic production, gentle groove, "
        f"leave clear space in the center for a lead vocal. "
        f"Create an approximately {dur}-second piece with a soft harmonium and "
        f"tanpura intro, tabla and dholak entering gently, and a calm outro."
    )


def build_exclude_styles() -> str:
    """Styles to explicitly avoid for a devotional track."""
    return "EDM, autotune, electric guitar, western drum kit, rap, distortion"
