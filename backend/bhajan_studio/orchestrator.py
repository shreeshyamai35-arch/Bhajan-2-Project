"""Pipeline orchestrator (Phase 1 backbone of the agentic design).

Runs the production stages in order and returns a structured result with a
per-stage log. Each stage here maps to an "agent" in AGENTIC_BUILD_PLAN.md;
Phase 2 will wrap these in a resumable state machine with human gates.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .audio import align, analysis, master, mix, qc
from .audio.io import load_mono, save_wav
from .config import SAMPLE_RATE, BhajanSpec
from .lyria.client import generate_instrumental
from .prompts.builder import build_instrumental_prompt
from .prompts.phonetics import correct_pronunciation


@dataclass
class StageLog:
    name: str
    ok: bool
    detail: str
    seconds: float


@dataclass
class PipelineResult:
    output_path: Path | None
    qc: qc.QCReport
    logs: list[StageLog] = field(default_factory=list)
    corrected_lyrics: str = ""
    pronunciation_changes: list[str] = field(default_factory=list)
    instrumental_source: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.qc.passed


def produce_bhajan(
    vocal_path: str | Path,
    spec: BhajanSpec,
    out_dir: str | Path,
    seed: int = 0,
) -> PipelineResult:
    logs: list[StageLog] = []
    notes: list[str] = []
    out_dir = Path(out_dir)

    def _run(name: str, fn):
        t0 = time.perf_counter()
        try:
            value = fn()
            logs.append(StageLog(name, True, "ok", time.perf_counter() - t0))
            return value
        except Exception as exc:
            logs.append(StageLog(name, False, str(exc), time.perf_counter() - t0))
            raise

    # 2. LyricPrep — phonetic correction
    corrected, changes = _run(
        "LyricPrep", lambda: correct_pronunciation(spec.lyrics)
    )

    # 3. VocalAnalysis
    vocal = _run("LoadVocal", lambda: load_mono(vocal_path))
    va = _run(
        "VocalAnalysis",
        lambda: analysis.analyze_vocal(vocal, spec.bpm, spec.key),
    )
    # Adopt detected tempo/key so the instrumental matches the real vocal.
    spec.bpm = float(va.detected_bpm or spec.bpm)
    spec.key = va.detected_key or spec.key
    notes.append(
        f"vocal {va.duration_s:.1f}s, bpm~{spec.bpm:.0f}, key~{spec.key}, "
        f"librosa={'yes' if va.used_librosa else 'no (fallback)'}"
    )

    # 4. PromptBuilder
    prompt = _run(
        "PromptBuilder",
        lambda: build_instrumental_prompt(spec, va.duration_s),
    )

    # 5. MusicGen (Lyria or mock)
    gen = _run(
        "MusicGen",
        lambda: generate_instrumental(spec, prompt, va.duration_s, seed=seed),
    )
    if gen.notes:
        notes.append(gen.notes)

    # 7. Alignment
    aligned = _run(
        "Alignment",
        lambda: align.align_vocal_and_instrumental(vocal, gen.audio_mono),
    )
    vocal_a, instr_a = aligned

    # 8. Mix
    bus = _run("Mix", lambda: mix.mix(vocal_a, instr_a))

    # 9. Master
    mres = _run("Master", lambda: master.master(bus))
    notes.append(
        f"master: {mres.input_lufs:.1f} -> {mres.output_lufs:.1f} LUFS, "
        f"peak {mres.peak_dbfs:.1f} dBFS"
    )

    # 10. QC
    report = _run(
        "QC",
        lambda: qc.run_qc(mres.audio, mres.output_lufs, va.duration_s),
    )

    # 12. Delivery
    safe = "".join(c if c.isalnum() else "_" for c in spec.title).strip("_") or "bhajan"
    out_path = out_dir / f"{safe}_master.wav"
    _run("Delivery", lambda: save_wav(out_path, mres.audio, SAMPLE_RATE))

    return PipelineResult(
        output_path=out_path,
        qc=report,
        logs=logs,
        corrected_lyrics=corrected,
        pronunciation_changes=changes,
        instrumental_source=gen.source,
        notes=notes,
    )
