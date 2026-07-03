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

**Phases 1–3 complete and verified.**
- **Phase 1** — core audio pipeline (align → mix → master → QC)
- **Phase 2** — agentic orchestration (job state machine + agents + human gates)
- **Phase 3** — web app (browser: record/upload → pick instrumental → download)

Runs end-to-end **today, offline**, via a built-in **mock instrumental** so the
whole product is testable without any API key. Set an API key to switch to real
**Lyria 3 Pro** — nothing else changes downstream.

Verified: full flow masters to exactly **-14.0 LUFS**, no clipping, QC pass;
browser audio (webm/opus) is transcoded via bundled ffmpeg.

### Live API status (important)

The Lyria integration is wired to the official Google endpoint
(`generativelanguage.googleapis.com/v1beta/interactions`, `x-goog-api-key`
auth). A valid key authenticates, **but Lyria music generation requires a
billing-enabled / paid tier** — a free-tier key returns HTTP **429 "not enough
quota"**, and the app cleanly **falls back to the mock** instrumental. Enable
Lyria billing on your Google account to get live AI audio; no code change
needed.

## Run the web app

```bash
cd backend
uv venv --python 3.11 .venv && . .venv/bin/activate
uv pip install -r requirements.txt

# optional: real Lyria (needs billing-enabled key)
export BHAJAN_API_KEY="your-google-api-key"

uvicorn bhajan_studio.web.app:app --host 0.0.0.0 --port 8000
# open http://localhost:8000  → record/upload a vocal, pick an instrumental,
# approve, download the mastered bhajan.
```

## Run the CLI (no browser)

```bash
cd backend && . .venv/bin/activate
python scripts/make_sample_vocal.py sample_vocal.wav        # test input
python -m bhajan_studio.cli --vocal sample_vocal.wav \
  --lyrics "Jai Shyam, Radhe Govind" --bpm 90 --key C \
  --taal keherwa --title "Shyam Bhajan" --out out
# -> out/Shyam_Bhajan_master.wav (mastered to -14 LUFS)
```

## Tests

```bash
cd backend && . .venv/bin/activate && python -m pytest -v
```
Covers phonetics, mastering to -14 LUFS, the full pipeline, and the full web
flow (create → candidates → select → finalize → approve → download).

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Mode (lyria/mock) + live Lyria probe |
| POST | `/api/jobs` | Create job (multipart: vocal + lyrics/bpm/key/taal/title) |
| GET | `/api/jobs/{id}` | Job status + stage logs + QC |
| GET | `/api/jobs/{id}/candidates/{i}` | Preview a candidate instrumental |
| POST | `/api/jobs/{id}/select` | Pick a candidate (human gate) → finalize |
| POST | `/api/jobs/{id}/approve` | Approve the master (human gate) |
| GET | `/api/jobs/{id}/download` | Download the final WAV |

> Note: Lyria audio carries an inaudible **SynthID** watermark. Never commit
> API keys — use `BHAJAN_API_KEY` (see `backend/.env.example`).

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
    orchestrator.py      # Phase 1 CLI pipeline (single-shot)
    cli.py               # command-line entry point
    prompts/             # phonetics + Lyria prompt builder
    lyria/               # Lyria REST client with mock fallback
    audio/               # io (ffmpeg decode), analysis, align, mix, master, qc
    jobs/                # Phase 2: Job model + state machine + runner (agents)
    web/                 # Phase 3: FastAPI app + static browser frontend
  scripts/               # make_sample_vocal.py (test input)
  tests/                 # pipeline + web end-to-end tests
  .env.example           # how to supply BHAJAN_API_KEY (never commit real keys)
.kiro/skills/bhajan-production/  # the production knowledge (Kiro skill)
AGENTIC_BUILD_PLAN.md    # full architecture + phased roadmap
```

## Roadmap

Phase 1 core ✅ → Phase 2 agentic orchestration ✅ → Phase 3 web app ✅ →
Phase 4 scale/auth/cloud storage → Phase 5 deploy (Cloud Run + Vercel/static).
See [`AGENTIC_BUILD_PLAN.md`](AGENTIC_BUILD_PLAN.md).

## Dependencies

- Core (offline): `numpy`, `soundfile`, `pyloudnorm`, `imageio-ffmpeg`
- Web: `fastapi`, `uvicorn`, `python-multipart`
- Optional: `librosa` (better tempo/key detection)
- Real music: a **billing-enabled** Google API key (Lyria 3 Pro)
