"""Job runner: drives a Job through the agent pipeline with human gates.

Stages map to the agents in AGENTIC_BUILD_PLAN.md:
  run_to_candidates() : LyricPrep -> VocalAnalysis -> PromptBuilder -> MusicGen
                        (stops at CANDIDATES_READY for human selection)
  finalize()          : Alignment -> Mix -> Master -> QC
                        (stops at AWAITING_APPROVAL, or QC_FAILED)
  approve()           : Delivery -> DELIVERED
"""
from __future__ import annotations

import time
from pathlib import Path

from ..audio import align, analysis, master as mastering, mix, qc
from ..audio.io import load_mono, save_wav
from ..config import BhajanSpec
from ..lyria.client import generate_candidates
from ..prompts.builder import build_instrumental_prompt
from ..prompts.phonetics import correct_pronunciation
from .model import Candidate, Job, JobState, JobStore


def _log(job: Job, name: str, ok: bool, detail: str, seconds: float) -> None:
    job.logs.append({"name": name, "ok": ok, "detail": detail,
                     "seconds": round(seconds, 4)})


def _spec_from_job(job: Job) -> BhajanSpec:
    return BhajanSpec(lyrics=job.lyrics, dialect=job.dialect, bpm=job.bpm,
                      key=job.key, taal=job.taal, title=job.title)


def run_to_candidates(job: Job, store: JobStore, n_candidates: int = 3,
                      seed: int = 0) -> Job:
    """Prep + generate candidate instrumentals; pause for human selection."""
    try:
        job.state = JobState.PREPPING.value
        store.save(job)

        # LyricPrep
        t0 = time.perf_counter()
        corrected, changes = correct_pronunciation(job.lyrics)
        job.corrected_lyrics, job.pronunciation_changes = corrected, changes
        _log(job, "LyricPrep", True, f"{len(changes)} fixes", time.perf_counter() - t0)

        # VocalAnalysis
        t0 = time.perf_counter()
        vocal = load_mono(job.vocal_path)
        va = analysis.analyze_vocal(vocal, job.bpm, job.key)
        job.bpm = float(va.detected_bpm or job.bpm)
        job.key = va.detected_key or job.key
        job.duration_s = va.duration_s
        _log(job, "VocalAnalysis", True,
             f"{va.duration_s:.1f}s bpm~{job.bpm:.0f} key~{job.key}",
             time.perf_counter() - t0)

        # PromptBuilder
        t0 = time.perf_counter()
        spec = _spec_from_job(job)
        job.prompt = build_instrumental_prompt(spec, va.duration_s)
        _log(job, "PromptBuilder", True, "ok", time.perf_counter() - t0)

        # MusicGen (candidates)
        job.state = JobState.GENERATING.value
        store.save(job)
        t0 = time.perf_counter()
        results = generate_candidates(spec, job.prompt, va.duration_s,
                                      n=n_candidates, seed=seed)
        jd = store.job_dir(job.id)
        job.candidates = []
        for i, r in enumerate(results):
            cpath = jd / f"candidate_{i}.wav"
            save_wav(cpath, r.audio_mono, r.sample_rate)
            job.candidates.append(
                Candidate(i, str(cpath), r.source, r.notes).__dict__)
        job.instrumental_source = results[0].source if results else ""
        for r in results:
            if r.notes and r.notes not in job.notes:
                job.notes.append(r.notes)
        _log(job, "MusicGen", True,
             f"{len(results)} candidates ({job.instrumental_source})",
             time.perf_counter() - t0)

        job.state = JobState.CANDIDATES_READY.value
        store.save(job)
    except Exception as e:  # pragma: no cover
        job.state = JobState.ERROR.value
        job.error = str(e)
        _log(job, "run_to_candidates", False, str(e), 0.0)
        store.save(job)
    return job


def finalize(job: Job, store: JobStore, candidate_index: int) -> Job:
    """Align chosen instrumental with the vocal, mix, master, QC."""
    try:
        if not (0 <= candidate_index < len(job.candidates)):
            raise IndexError(f"invalid candidate index {candidate_index}")
        job.selected_index = candidate_index
        job.state = JobState.FINALIZING.value
        store.save(job)

        vocal = load_mono(job.vocal_path)
        instrumental = load_mono(job.candidates[candidate_index]["path"])

        t0 = time.perf_counter()
        vocal_a, instr_a = align.align_vocal_and_instrumental(vocal, instrumental)
        _log(job, "Alignment", True, "ok", time.perf_counter() - t0)

        t0 = time.perf_counter()
        bus = mix.mix(vocal_a, instr_a)
        _log(job, "Mix", True, "ok", time.perf_counter() - t0)

        t0 = time.perf_counter()
        mres = mastering.master(bus)
        _log(job, "Master", True,
             f"{mres.input_lufs:.1f}->{mres.output_lufs:.1f} LUFS",
             time.perf_counter() - t0)

        t0 = time.perf_counter()
        report = qc.run_qc(mres.audio, mres.output_lufs, job.duration_s)
        job.qc = {"passed": report.passed, "checks": report.checks,
                  "metrics": report.metrics, "failures": report.failures}
        _log(job, "QC", report.passed, report.summary().splitlines()[0],
             time.perf_counter() - t0)

        safe = "".join(c if c.isalnum() else "_" for c in job.title).strip("_") or "bhajan"
        out_path = store.job_dir(job.id) / f"{safe}_master.wav"
        save_wav(out_path, mres.audio)
        job.master_path = str(out_path)

        job.state = (JobState.AWAITING_APPROVAL.value if report.passed
                     else JobState.QC_FAILED.value)
        store.save(job)
    except Exception as e:  # pragma: no cover
        job.state = JobState.ERROR.value
        job.error = str(e)
        _log(job, "finalize", False, str(e), 0.0)
        store.save(job)
    return job


def approve(job: Job, store: JobStore) -> Job:
    """Human approval gate -> mark delivered."""
    if job.state != JobState.AWAITING_APPROVAL.value:
        raise ValueError(f"cannot approve from state {job.state}")
    job.state = JobState.DELIVERED.value
    _log(job, "Delivery", True, "approved", 0.0)
    store.save(job)
    return job
