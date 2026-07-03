"""End-to-end web test using FastAPI's in-process TestClient (offline/mock).

Exercises the full agentic flow through the HTTP API:
create job -> poll to candidates -> select -> finalize -> approve -> download.
Runs in mock mode (no API key) so it is deterministic and offline.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fastapi.testclient import TestClient  # noqa: E402

from bhajan_studio.audio.io import load_mono, save_wav  # noqa: E402
from bhajan_studio.web.app import app  # noqa: E402
from make_sample_vocal import make_sample_vocal  # noqa: E402


def _wait_for(client, job_id, state, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["state"] == state:
            return job
        if job["state"] in {"error", "qc_failed"}:
            raise AssertionError(f"job ended in {job['state']}: {job.get('error')}")
        time.sleep(0.3)
    raise AssertionError(f"timeout waiting for state {state}")


def test_web_end_to_end(tmp_path, monkeypatch):
    # Ensure mock mode (no live key) for a deterministic offline test.
    for var in ("BHAJAN_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    client = TestClient(app)

    assert client.get("/").status_code == 200
    assert client.get("/api/health").json()["status"] == "ok"

    vocal_path = tmp_path / "vocal.wav"
    save_wav(vocal_path, make_sample_vocal(seconds=10.0, key="C"))

    with vocal_path.open("rb") as f:
        res = client.post(
            "/api/jobs",
            files={"vocal": ("vocal.wav", f, "audio/wav")},
            data={"title": "Web Test Bhajan", "lyrics": "Jai Shyam Radhe",
                  "bpm": "90", "key": "C", "taal": "keherwa"},
        )
    assert res.status_code == 201, res.text
    job_id = res.json()["id"]

    job = _wait_for(client, job_id, "candidates_ready")
    assert len(job["candidates"]) == 3

    # candidate audio is downloadable
    assert client.get(f"/api/jobs/{job_id}/candidates/0").status_code == 200

    assert client.post(f"/api/jobs/{job_id}/select", data={"index": "0"}).status_code == 200
    _wait_for(client, job_id, "awaiting_approval")

    approved = client.post(f"/api/jobs/{job_id}/approve").json()
    assert approved["state"] == "delivered"
    assert approved["qc"]["passed"] is True

    dl = client.get(f"/api/jobs/{job_id}/download")
    assert dl.status_code == 200
    out = tmp_path / "master.wav"
    out.write_bytes(dl.content)
    audio = load_mono(out)
    assert 9.0 <= audio.size / 44100 <= 11.0
