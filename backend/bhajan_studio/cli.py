"""Command-line entry point for the Phase 1 pipeline.

Usage:
    python -m bhajan_studio.cli --vocal path/to/vocal.wav \
        --lyrics "Shyam teri bansi..." --bpm 90 --key C --taal keherwa \
        --title "Shyam Bhajan" --out out/

If GEMINI_API_KEY is set the instrumental comes from Lyria 3 Pro; otherwise a
local devotional mock instrumental is used so the pipeline runs offline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import BhajanSpec
from .orchestrator import produce_bhajan


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bhajan Studio - produce a bhajan from a vocal")
    p.add_argument("--vocal", required=True, help="Path to the recorded vocal (WAV)")
    p.add_argument("--lyrics", default="", help="Lyrics text (for phonetic prep)")
    p.add_argument("--bpm", type=float, default=90.0)
    p.add_argument("--key", default="C")
    p.add_argument("--taal", default="keherwa", choices=["keherwa", "dadra", "bhajani"])
    p.add_argument("--dialect", default="hindi", choices=["hindi", "braj", "rajasthani"])
    p.add_argument("--title", default="Untitled Bhajan")
    p.add_argument("--out", default="out", help="Output directory")
    p.add_argument("--seed", type=int, default=0)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not Path(args.vocal).exists():
        print(f"error: vocal file not found: {args.vocal}", file=sys.stderr)
        return 2

    spec = BhajanSpec(
        lyrics=args.lyrics,
        dialect=args.dialect,
        bpm=args.bpm,
        key=args.key,
        taal=args.taal,
        title=args.title,
    )

    result = produce_bhajan(args.vocal, spec, args.out, seed=args.seed)

    print("=" * 60)
    print(f"Bhajan Studio - {spec.title}")
    print("=" * 60)
    print(f"instrumental source : {result.instrumental_source}")
    if result.pronunciation_changes:
        print(f"pronunciation fixes : {', '.join(result.pronunciation_changes)}")
    for note in result.notes:
        print(f"note                : {note}")
    print("-" * 60)
    for log in result.logs:
        flag = "ok" if log.ok else "XX"
        print(f"  [{flag}] {log.name:<14} {log.seconds*1000:7.1f} ms  {log.detail}")
    print("-" * 60)
    print(result.qc.summary())
    print(f"metrics             : {result.qc.metrics}")
    if result.output_path:
        print(f"output              : {result.output_path}")
    print("=" * 60)

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
