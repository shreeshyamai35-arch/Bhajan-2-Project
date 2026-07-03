"""Hindi / Braj / Rajasthani phonetic correction for AI singers.

AI singers pronounce, they don't read. Devotional names are the highest
failure rate. We respell them the way they must be SUNG so pronunciation
stays correct. Mirrors the cheat-sheet in the bhajan-production skill.
"""
from __future__ import annotations

import re

# Intended spelling -> sung respelling. Applied case-insensitively as whole
# words. Keep the most common Shyam/Krishna devotional vocabulary here.
PHONETIC_MAP: dict[str, str] = {
    "shyam": "Shyaam",
    "radhe": "Raa-dhe",
    "radha": "Raa-dhaa",
    "govind": "Go-vind",
    "govinda": "Go-vin-da",
    "krishna": "Krish-na",
    "krsna": "Krish-na",
    "murli": "Mur-lee",
    "murari": "Mu-raa-ri",
    "banke": "Baanke",
    "bihari": "Bihaari",
    "khatu": "Khaatoo",
    "hare": "Ha-re",
    "mohan": "Mo-han",
    "girdhar": "Gir-dhar",
    "giridhar": "Gi-ri-dhar",
    "jai": "Jai",
    "shri": "Shree",
    "bhajan": "Bha-jan",
    "keshav": "Ke-shav",
    "madhav": "Maa-dhav",
    "gopal": "Go-paal",
    "nandlal": "Nand-laal",
    "shyama": "Shyaa-ma",
}


def correct_pronunciation(lyrics: str) -> tuple[str, list[str]]:
    """Return (respelled lyrics, list of changes made).

    Only whole-word, case-insensitive matches are replaced, preserving the
    surrounding text and line breaks.
    """
    changes: list[str] = []

    def _replace(match: re.Match) -> str:
        word = match.group(0)
        repl = PHONETIC_MAP.get(word.lower())
        if repl and repl.lower() != word.lower():
            changes.append(f"{word} -> {repl}")
            return repl
        return word

    pattern = re.compile(r"[A-Za-z]+")
    corrected = pattern.sub(_replace, lyrics)
    return corrected, changes
