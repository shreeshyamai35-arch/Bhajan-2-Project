"""FastAPI web app for Bhajan Studio (Phase 3).

A singer uploads/records a vocal + fills in lyrics/tempo/key; the agent
pipeline generates candidate instrumentals (Lyria or mock), the user picks
one, and the app aligns + mixes + masters the real vocal on top, gated by an
automated QC check and a human approval step, then serves the final download.

Run:  uvicorn bhajan_studio.web.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import shutil
import threading
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from ..lyria.client import get_api_key, live_probe
from ..jobs.model import JobState, JobStore
from ..jobs.runner import approve, finalize, run_to_candidates

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data" / "jobs"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Bhajan Studio", version="0.2.0")
store = JobStore(DATA_DIR)


def _bg(fn, *args, **kwargs) -> None:
    threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True).start()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "mode": "lyria" if get_api_key() else "mock",
        "lyria": live_probe(),
    }


@app.post("/api/jobs")
async def create_job(
    vocal: UploadFile,
    lyrics: str = Form(""),
    bpm: float = Form(90.0),
    key: str = Form("C"),
    taal: str = Form("keherwa"),
    dialect: str = Form("hindi"),
    title: str = Form("Untitled Bhajan"),
) -> JSONResponse:
    job = store.create(title=title, lyrics=lyrics, bpm=bpm, key=key,
                       taal=taal, dialect=dialect)
    # Persist the uploaded vocal, preserving extension for ffmpeg decoding.
    ext = Path(vocal.filename or "vocal.wav").suffix or ".wav"
    dest = store.job_dir(job.id) / f"vocal{ext}"
    with dest.open("wb") as f:
        shutil.copyfileobj(vocal.file, f)
    job.vocal_path = str(dest)
    store.save(job)

    _bg(run_to_candidates, job, store)
    return JSONResponse(job.to_public(), status_code=201)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = store.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job.to_public()


@app.get("/api/jobs/{job_id}/candidates/{index}")
def get_candidate(job_id: str, index: int) -> FileResponse:
    job = store.get(job_id)
    if not job or not (0 <= index < len(job.candidates)):
        raise HTTPException(404, "candidate not found")
    return FileResponse(job.candidates[index]["path"], media_type="audio/wav")


@app.post("/api/jobs/{job_id}/select")
def select_candidate(job_id: str, index: int = Form(...)) -> dict:
    job = store.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job.state != JobState.CANDIDATES_READY.value:
        raise HTTPException(409, f"cannot select from state {job.state}")
    _bg(finalize, job, store, index)
    return {"ok": True, "state": JobState.FINALIZING.value}


@app.post("/api/jobs/{job_id}/approve")
def approve_job(job_id: str) -> dict:
    job = store.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    try:
        approve(job, store)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return job.to_public()


@app.get("/api/jobs/{job_id}/download")
def download(job_id: str) -> FileResponse:
    job = store.get(job_id)
    if not job or not job.master_path or not Path(job.master_path).exists():
        raise HTTPException(404, "master not ready")
    fname = Path(job.master_path).name
    return FileResponse(job.master_path, media_type="audio/wav", filename=fname)
