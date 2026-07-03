# Bhajan Studio

Turn a singer's **raw recorded vocal** into a professional, streaming-ready
devotional **bhajan** using AI — affordably.

The singer's **real voice stays untouched**. Google **Lyria 3 Pro** (official
API) generates the *instrumental* backing at a matched tempo/key, and this
pipeline **aligns → mixes → masters** the real vocal on top, then runs an
automated **quality gate** (loudness, clipping, tempo-lock, pronunciation).

> Why not just "vocal → AI song"? Suno can do that but has **no official API**.
> Lyria has an official API but only does **text/image → music** (it makes its
> own voice). So we use Lyria for the **instrumental** and keep the real voice.
> Full reasoning + roadmap in [`AGENTIC_BUILD_PLAN.md`](AGENTIC_BUILD_PLAN.md).

## Status

**Phase 1 — core pipeline (this repo).** Runs end-to-end today, offline, with a
built-in **mock instrumental** so you can test without any API key. Add a
`GEMINI_API_KEY` to switch to the real Lyria 3 Pro instrumental — nothing else
changes downstream.

Verified: sample run masters to exactly **-14.0 LUFS**, no clipping, QC pass.

## Quick start

```bash
cd backend
uv venv --python 3.11 .venv && . .venv/bin/activate
uv pip install numpy soundfile pyloudnorm pytest   # core (runs offline)

# 1) make a throwaway synthetic "vocal" to test with
python scripts/make_sample_vocal.py sample_vocal.wav

# 2) produce a bhajan from it
python -m bhajan_studio.cli \
  --vocal sample_vocal.wav \
  --lyrics "Jai Shyam, Radhe Govind, Krishna Murari" \
  --bpm 90 --key C --taal keherwa --title "Shyam Bhajan" --out out

# 3) result: out/Shyam_Bhajan_master.wav  (mastered to -14 LUFS)
```

Run the tests:

```bash
cd backend && . .venv/bin/activate && python -m pytest -v
```

## Using the real Lyria 3 Pro instrumental

1. Get a Google **Gemini API key** with Lyria access
   (Google AI Studio / Vertex AI).
2. Install the SDK and set the key:
   ```bash
   uv pip install google-genai
   export GEMINI_API_KEY="your-key"
   ```
3. Run the same CLI. The instrumental now comes from Lyria 3 Pro
   (`instrumental source : lyria`). If the call fails for any reason, the
   pipeline automatically falls back to the mock so it never hard-fails.

> Note: Lyria audio carries an inaudible **SynthID** watermark.

## How it works (pipeline stages)

Each stage maps to an "agent" in the build plan:

| Stage | Module | What it does |
|-------|--------|--------------|
| LyricPrep | `prompts/phonetics.py` | Fixes sung pronunciation (Shyam → Shyaam) |
| VocalAnalysis | `audio/analysis.py` | Duration, loudness, tempo/key (librosa optional) |
| PromptBuilder | `prompts/builder.py` | Builds the Lyria instrumental-only prompt |
| MusicGen | `lyria/client.py` | Lyria 3 Pro instrumental (or mock) |
| Alignment | `audio/align.py` | Fits instrumental to the vocal length |
| Mix | `audio/mix.py` | Vocal on top + light temple reverb |
| Master | `audio/master.py` | Normalise to -14 LUFS, peak ≤ -1 dBFS |
| QC | `audio/qc.py` | Loudness / clipping / silence / duration gate |

Orchestrated by `bhajan_studio/orchestrator.py`; CLI in `bhajan_studio/cli.py`.

## Project layout

```
backend/
  bhajan_studio/
    config.py            # constants + BhajanSpec
    orchestrator.py      # runs the stages, returns a logged result
    cli.py               # command-line entry point
    prompts/             # phonetics + Lyria prompt builder
    lyria/               # Lyria client with mock fallback
    audio/               # io, analysis, align, mix, master, qc
  scripts/               # make_sample_vocal.py (test input)
  tests/                 # end-to-end + unit tests
.kiro/skills/bhajan-production/  # the production knowledge (Kiro skill)
AGENTIC_BUILD_PLAN.md    # full architecture + phased roadmap
```

## Roadmap

Phase 1 core (done) → Phase 2 agentic orchestration (resumable + human gates)
→ Phase 3 web app (Next.js + FastAPI) → Phase 4 scale/auth → Phase 5 deploy.
See [`AGENTIC_BUILD_PLAN.md`](AGENTIC_BUILD_PLAN.md).

## Dependencies

- Core (runs offline): `numpy`, `soundfile`, `pyloudnorm`
- Optional: `librosa` (better tempo/key detection), `google-genai` (real Lyria)
