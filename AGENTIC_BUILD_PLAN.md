# Bhajan Studio — Agentic Web App Build Plan

An AI-powered web app that turns a singer's raw recorded vocal into a
professional, streaming-ready devotional bhajan.

**Core idea:** Keep the singer's REAL voice untouched. Use Google **Lyria 3 Pro**
(official API) to generate the *instrumental* backing at a matched tempo/key, then
our own pipeline **aligns + mixes + masters** the real vocal on top.

---

## 1. Why this architecture (the key decision)

| Option | Does "real voice → AI music"? | Official API | Verdict |
|---|---|---|---|
| Suno "Add Instrumentals" | Yes (true SAG) | ❌ No (risky 3rd-party only) | Manual A/B testing only |
| **Lyria 3 Pro** | No (makes its own voice) | ✅ Yes (Gemini/Vertex) | **Product backbone** |

Lyria accepts **text/images only — no audio input** — and generates its own vocals.
So we use it for **instrumental-only** generation and layer the real vocal ourselves.
This is *better* for voice fidelity (the real voice is never re-timed or colored) and
runs on a stable, official API we can build a product on.

**Non-negotiables**
- Real singer's voice is never replaced or cloned.
- Only official APIs in the production path.
- Human approval gates at candidate-selection and final-release.
- A hard QC gate (loudness, clipping, tempo-lock, pronunciation) — nothing ships that fails.

---

## 2. High-level architecture

```
                          ┌──────────────────────────────────────────┐
   Browser (Next.js)      │                Backend (FastAPI)          │
 ┌───────────────────┐    │  ┌───────────┐   ┌──────────────────────┐ │
 │ Record / upload   │    │  │  REST API │   │  Job Queue (Redis/RQ)│ │
 │ vocal + lyrics    │───▶│  │  /jobs    │──▶│  async workers       │ │
 │ pick BPM/key/taal │    │  └───────────┘   └──────────┬───────────┘ │
 │ live progress     │◀───│         ▲                   │             │
 │ preview + download│    │         │            ┌──────▼───────────┐ │
 └───────────────────┘    │    status/SSE        │ Agent Orchestrator│ │
                          │         │            │ (state machine)   │ │
                          │         └────────────┤  runs the agents  │ │
                          │                      └──────┬───────────┘ │
                          └─────────────────────────────┼─────────────┘
                                                        │
        ┌───────────────────────────────────────────────┼───────────────────┐
        ▼                    ▼                ▼          ▼          ▼         ▼
   Lyria 3 Pro API      Vocal analysis    Alignment    Mixing    Mastering   QC
   (instrumental)       (librosa)         (align)      (pydub)   (-14 LUFS)  (auto)
        │                                                                     │
        └───────────────── Object Storage (audio files) + DB (job metadata) ─┘
```

---

## 3. Tech stack (with rationale)

| Layer | Choice | Why |
|---|---|---|
| Frontend | **Next.js + TypeScript + Tailwind** | Web recording (MediaRecorder), upload, live job progress, audio preview/download. Deployable on Vercel. |
| Backend/API | **Python + FastAPI** | The Lyria SDK (`google-genai`) and all audio libs are Python-native. Async-friendly. |
| Agent orchestration | **LangGraph** (or a light custom state machine) | Deterministic, resumable multi-step pipeline with retries + human-in-loop gates. |
| Async jobs | **Redis + RQ** (or Celery) | Generation + mastering take time; must run off the request thread. |
| Audio DSP | **librosa, pydub, soundfile, pyloudnorm** + **ffmpeg** | BPM/key detection, alignment, mixing, LUFS mastering. |
| Music gen | **Lyria 3 Pro** via `google-genai` | Official API, WAV output, Hindi, instrumental-only. |
| LLM (prompt/phonetics) | **Gemini** via `google-genai` | Build Lyria prompts + Hindi/Braj phonetic correction. |
| Storage | **Local (dev) → GCS/S3 (prod)** | Store uploads, stems, masters. |
| DB | **SQLite (dev) → Postgres (prod)** | Job + track metadata. |
| Deploy | Frontend: **Vercel** · Backend: **Google Cloud Run** | Cloud Run keeps you close to Lyria/GCP + scales to zero. |

> Note: These are sensible defaults. If you have team preferences (e.g., a different
> frontend framework), tell me and I'll adapt the plan.

---

## 4. The agentic pipeline

Each stage is an **agent** with one job, its own tools, and a pass/fail output.
The **Orchestrator** runs them in order, retries failures, and pauses at human gates.

| # | Agent | Input | What it does | Tools |
|---|---|---|---|---|
| 1 | **IntakeAgent** | Lyrics, dialect, uploaded vocal, chosen BPM/key/taal | Validates inputs, creates a job record | FastAPI, DB |
| 2 | **LyricPrepAgent** | Lyrics + dialect | Meter map + phonetic correction (Shyaam/Raadhe…), section tags (Sthayi/Antara) | Gemini + phonetic sheet |
| 3 | **VocalAnalysisAgent** | Raw vocal | Detect BPM + key, trim silence, denoise, measure loudness | librosa, ffmpeg |
| 4 | **PromptBuilderAgent** | Style + detected BPM/key + taal | Builds the Lyria "instrumental-only" prompt (harmonium/tabla/dholak/bansuri, taal, BPM, key) | Gemini + skill template |
| 5 | **MusicGenAgent** | Prompt | Calls Lyria 3 Pro → N instrumental candidates (WAV) | Lyria API |
| 6 | **[HUMAN GATE] SelectAgent** | N candidates | Producer previews + picks best (or auto-rank by tempo/key match) | Frontend |
| 7 | **AlignmentAgent** | Vocal + chosen instrumental | Time-align vocal to instrumental (offset + tempo lock), layer | librosa, pydub |
| 8 | **MixAgent** | Aligned stems | Balance levels (vocal on top), light hall reverb, EQ | pydub/ffmpeg filters |
| 9 | **MasterAgent** | Mix | Normalize to **-14 LUFS**, true-peak ≤ -1 dBTP, WAV+MP3 | pyloudnorm, ffmpeg |
| 10 | **QCAgent** | Master | Auto-check: loudness, clipping, silence, tempo-lock, duration | pyloudnorm, librosa |
| 11 | **[HUMAN GATE] ApproveAgent** | QC report + preview | Producer approves or sends back to regenerate | Frontend |
| 12 | **DeliveryAgent** | Approved master | Store, tag metadata, expose download links | Storage, DB |

**Retry logic:** if QCAgent fails (e.g., tempo mismatch, low loudness), the Orchestrator
loops back to MusicGenAgent (regenerate) or MasterAgent (re-master), up to N tries,
then escalates to the human.

---

## 5. Job lifecycle (state machine)

```
CREATED → LYRICS_PREPPED → VOCAL_ANALYZED → PROMPT_BUILT → GENERATING
   → CANDIDATES_READY → [human picks] → ALIGNING → MIXING → MASTERING
   → QC_RUNNING → QC_PASSED → [human approves] → DELIVERED
                     └── QC_FAILED → (retry) ──┘
```

Every state is persisted, so a job is resumable and the UI can show live progress via SSE/WebSocket.

---

## 6. Repo structure

```
bhajan-studio/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + routes
│   │   ├── jobs/                   # queue, worker, job model
│   │   ├── agents/                 # one file per agent (intake, lyricprep, ...)
│   │   ├── orchestrator/           # LangGraph/state-machine wiring
│   │   ├── audio/                  # analysis, align, mix, master, qc utils
│   │   ├── lyria/                  # Lyria client wrapper
│   │   ├── prompts/                # prompt + phonetic templates (from the skill)
│   │   └── storage/                # local/GCS adapters
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/                        # Next.js routes (record, job, result)
│   ├── components/                 # recorder, progress, player
│   └── package.json
├── .kiro/skills/bhajan-production/ # the production knowledge (already created)
└── AGENTIC_BUILD_PLAN.md           # this file
```

---

## 7. API endpoints (v1)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/jobs` | Create job (multipart: vocal file + lyrics + params) |
| GET | `/api/jobs/{id}` | Job status + current state |
| GET | `/api/jobs/{id}/events` | SSE live progress stream |
| GET | `/api/jobs/{id}/candidates` | List instrumental candidates |
| POST | `/api/jobs/{id}/select` | Pick a candidate (human gate) |
| POST | `/api/jobs/{id}/approve` | Approve final master (human gate) |
| GET | `/api/jobs/{id}/download` | Download final WAV/MP3 |

---

## 8. Phased roadmap (milestones + acceptance criteria)

### Phase 0 — Spike (½ day)
- Get a Gemini API key; call Lyria 3 Pro once for a 30s Hindi devotional instrumental.
- **Done when:** we have a real `.wav` instrumental from the API on disk.

### Phase 1 — Core pipeline as a CLI (backbone)
- `vocal.wav + lyrics + BPM/key` → instrumental (Lyria) → align → mix → master → `output.wav`.
- Add ffmpeg; implement VocalAnalysis, Alignment, Mix, Master, QC as plain functions.
- **Done when:** one command produces a mastered bhajan at -14 LUFS that passes QC.

### Phase 2 — Agentic orchestration
- Wrap the functions as agents; add the Orchestrator state machine with retries + human gates.
- **Done when:** the pipeline runs stage-by-stage, is resumable, and logs each agent's pass/fail.

### Phase 3 — Web app
- FastAPI + job queue; Next.js frontend (record/upload, live progress, candidate selection, preview, download).
- **Done when:** a non-technical singer can make a bhajan end-to-end in the browser.

### Phase 4 — Quality & scale
- Multi-user, auth, cloud storage, better QC (pronunciation check), premium "real-instrument overdub" flow.
- **Done when:** multiple users run concurrent jobs reliably.

### Phase 5 — Deploy
- Backend → Cloud Run; frontend → Vercel; managed Redis + Postgres + object storage.
- **Done when:** it's live on a URL you can share.

---

## 9. Costs (rough)

- **Lyria API**: per-generation (check current Lyria 3 pricing) — a few generations per song.
- **Hosting**: Cloud Run scales to zero (cheap at low volume) + Vercel free/hobby tier.
- **Per-bhajan running cost**: dominated by a handful of Lyria calls — far below the ₹10k–50k studio cost.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Vocal recorded without a click → tempo drift, won't align | Enforce click-track recording in the UI; VocalAnalysis flags drift and warns |
| Lyria instrumental doesn't "feel" devotional enough | Strong prompt templates from the skill; generate multiple candidates; premium real-instrument overdub path |
| SynthID watermark on Lyria audio | Inaudible; acceptable for release. Document it for transparency |
| Lyria single-turn (no editing) | Treat generations like takes; regenerate rather than edit |
| API/pricing changes | Wrap Lyria behind our `lyria/` adapter so we can swap providers |

---

## 11. What you need to provide

1. A **Google Gemini / Google Cloud API key** with Lyria access (I'll include setup steps).
2. Confirm **dialect** for the phonetic module (Hindi + Braj/Rajasthani assumed).
3. Any **team tech preferences** (else I proceed with the stack above).

---

## 12. Immediate next step

Scaffold **Phase 0 + Phase 1**: project skeleton + a working script that calls Lyria for a
devotional instrumental and runs the align→mix→master→QC chain on a sample vocal.
```
