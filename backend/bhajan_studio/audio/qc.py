"""Automated quality gate. Nothing ships that fails these checks.

Mirrors the QC section of the bhajan-production skill (audio portion):
loudness on target, no clipping, not mostly silent, sensible duration.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import (LUFS_TOLERANCE, MAX_PEAK_DBFS, MIN_ACTIVE_RATIO,
                      SAMPLE_RATE, TARGET_LUFS)


@dataclass
class QCReport:
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"QC: {status}"]
        for name, ok in self.checks.items():
            mark = "ok" if ok else "XX"
            lines.append(f"  [{mark}] {name}")
        if self.failures:
            lines.append("  failures: " + "; ".join(self.failures))
        return "\n".join(lines)


def run_qc(stereo: np.ndarray, output_lufs: float, expected_duration_s: float,
           sr: int = SAMPLE_RATE) -> QCReport:
    checks: dict[str, bool] = {}
    metrics: dict[str, float] = {}
    failures: list[str] = []

    # Loudness on target
    lufs_ok = abs(output_lufs - TARGET_LUFS) <= LUFS_TOLERANCE
    checks["loudness_-14_LUFS"] = lufs_ok
    metrics["output_lufs"] = round(output_lufs, 2)
    if not lufs_ok:
        failures.append(f"loudness {output_lufs:.2f} LUFS off target {TARGET_LUFS}")

    # No clipping
    peak = float(np.max(np.abs(stereo))) if stereo.size else 0.0
    peak_dbfs = 20.0 * np.log10(peak) if peak > 0 else float("-inf")
    peak_ok = peak_dbfs <= MAX_PEAK_DBFS
    checks["no_clipping"] = peak_ok
    metrics["peak_dbfs"] = round(peak_dbfs, 2)
    if not peak_ok:
        failures.append(f"peak {peak_dbfs:.2f} dBFS exceeds {MAX_PEAK_DBFS}")

    # Not mostly silent
    mono = stereo.mean(axis=0) if stereo.ndim == 2 else stereo
    active_ratio = float(np.mean(np.abs(mono) > 0.005)) if mono.size else 0.0
    active_ok = active_ratio >= MIN_ACTIVE_RATIO
    checks["not_silent"] = active_ok
    metrics["active_ratio"] = round(active_ratio, 3)
    if not active_ok:
        failures.append(f"only {active_ratio:.0%} active audio")

    # Duration sanity (tempo-lock proxy: output matches the sung length)
    dur = (mono.size / sr) if mono.size else 0.0
    dur_ok = abs(dur - expected_duration_s) <= 0.5
    checks["duration_matches_vocal"] = dur_ok
    metrics["duration_s"] = round(dur, 2)
    if not dur_ok:
        failures.append(
            f"duration {dur:.2f}s vs expected {expected_duration_s:.2f}s"
        )

    passed = all(checks.values())
    return QCReport(passed=passed, checks=checks, metrics=metrics, failures=failures)
