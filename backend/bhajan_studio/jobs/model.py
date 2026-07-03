"""Job model + state machine + file-backed store (Phase 2 agentic layer).

A Job is the unit of work that flows through the agent pipeline. It is
persisted as JSON so the pipeline is resumable and the web layer can poll
status. Audio artifacts live on disk next to the job metadata.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path


def _json_default(o):
    """Fallback encoder so stray numpy scalars/arrays never break persistence."""
    if hasattr(o, "item"):        # numpy scalar
        return o.item()
    if hasattr(o, "tolist"):      # numpy array
        return o.tolist()
    return str(o)


class JobState(str, Enum):
    CREATED = "created"
    PREPPING = "prepping"            # lyric prep + vocal analysis + prompt
    GENERATING = "generating"        # Lyria/mock candidates
    CANDIDATES_READY = "candidates_ready"   # HUMAN GATE: pick one
    FINALIZING = "finalizing"        # align + mix + master + qc
    AWAITING_APPROVAL = "awaiting_approval"  # HUMAN GATE: approve master
    DELIVERED = "delivered"
    QC_FAILED = "qc_failed"
    ERROR = "error"


@dataclass
class Candidate:
    index: int
    path: str
    source: str          # "lyria" | "mock"
    notes: str = ""


@dataclass
class Job:
    id: str
    title: str
    state: str = JobState.CREATED.value
    # inputs
    lyrics: str = ""
    dialect: str = "hindi"
    bpm: float = 90.0
    key: str = "C"
    taal: str = "keherwa"
    vocal_path: str = ""
    # derived / outputs
    corrected_lyrics: str = ""
    pronunciation_changes: list[str] = field(default_factory=list)
    duration_s: float = 0.0
    prompt: str = ""
    instrumental_source: str = ""
    candidates: list[dict] = field(default_factory=list)
    selected_index: int | None = None
    master_path: str = ""
    qc: dict = field(default_factory=dict)
    logs: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_public(self) -> dict:
        """JSON-safe view for the API (hides absolute filesystem paths)."""
        d = asdict(self)
        d.pop("vocal_path", None)
        d.pop("master_path", None)
        d["candidates"] = [
            {"index": c["index"], "source": c["source"], "notes": c.get("notes", "")}
            for c in self.candidates
        ]
        d["has_master"] = bool(self.master_path)
        return d


class JobStore:
    """Simple file-backed store: data/jobs/<id>/job.json + audio artifacts."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        d = self.root / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def create(self, **kwargs) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], **kwargs)
        self.save(job)
        return job

    def save(self, job: Job) -> None:
        job.updated_at = time.time()
        path = self.job_dir(job.id) / "job.json"
        path.write_text(json.dumps(asdict(job), indent=2, default=_json_default))

    def get(self, job_id: str) -> Job | None:
        path = self.root / job_id / "job.json"
        if not path.exists():
            return None
        return Job(**json.loads(path.read_text()))
