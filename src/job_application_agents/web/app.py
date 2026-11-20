"""Web front end for the JobApplicationAgents crew.

POST a job URL + resume PDF -> the crew runs in a background thread -> poll for
progress and the four reports. Start with:  uv run web   (or .venv\\Scripts\\web.exe)
"""
import os

# Must run before anything creates an SSL context (see README > Troubleshooting).
os.environ.pop("SSLKEYLOGFILE", None)

import truststore

truststore.inject_into_ssl()

import io
import re
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pypdfium2 as pdfium
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from job_application_agents.crew import JobApplicationAgents

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = "runs"  # relative to PROJECT_ROOT; CrewAI requires relative output paths
STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_PDF_BYTES = 5 * 1024 * 1024
MIN_RESUME_CHARS = 200

# Task name -> key used by the UI. Order matches the sequential crew.
STEPS = [
    ("analyze_job_task", "job_brief", "Analyzing the job posting"),
    ("tailor_resume_task", "tailored_resume", "Tailoring your resume"),
    ("cover_letter_task", "cover_letter", "Writing the cover letter"),
    ("interview_prep_task", "interview_prep", "Preparing interview questions"),
    ("match_report_task", "match_report", "Scoring the application"),
]

load_dotenv(PROJECT_ROOT / ".env")
os.chdir(PROJECT_ROOT)

app = FastAPI(title="Job Application Agents")
_runs: dict[str, dict] = {}
_runs_lock = threading.Lock()
_crew_slot = threading.Semaphore(1)  # one crew at a time: protects API spend and CPU


def _update(run_id: str, **fields) -> None:
    with _runs_lock:
        _runs[run_id].update(fields)


def _extract_pdf_text(data: bytes) -> str:
    pdf = pdfium.PdfDocument(io.BytesIO(data))
    try:
        pages = []
        for page in pdf:
            textpage = page.get_textpage()
            pages.append(textpage.get_text_range())
            textpage.close()
            page.close()
        return "\n\n".join(pages).replace("\r\n", "\n").strip()
    finally:
        pdf.close()


def _parse_score(markdown: str) -> int | None:
    m = re.search(r"match\s*score\W*(\d{1,3})\s*/\s*100", markdown, re.I)
    return int(m.group(1)) if m else None


def _run_crew(run_id: str, job_url: str, resume_path: str, out_dir: str) -> None:
    try:
        _update(run_id, status="running", step=0)
        crew = JobApplicationAgents(resume_path=resume_path, output_dir=out_dir).crew()
        done = {"n": 0}

        def on_task_done(output) -> None:
            i = done["n"]
            done["n"] += 1
            key = STEPS[i][1] if i < len(STEPS) else f"task_{i}"
            with _runs_lock:
                _runs[run_id]["results"][key] = output.raw
                _runs[run_id]["step"] = done["n"]

        crew.task_callback = on_task_done  # live progress only; may fire asynchronously
        output = crew.kickoff(inputs={"job_url": job_url})

        # Authoritative final results come from kickoff's return value.
        keys = {name: key for name, key, _ in STEPS}
        final = {keys.get(t.name, t.name): t.raw for t in output.tasks_output}
        with _runs_lock:
            _runs[run_id]["results"].update(final)
            results = _runs[run_id]["results"]
            _runs[run_id]["score"] = _parse_score(results.get("match_report", ""))
            _runs[run_id]["status"] = "done"
            _runs[run_id]["step"] = len(STEPS)
    except Exception as e:  # surface the failure to the UI; full trace to the console
        traceback.print_exc()
        _update(run_id, status="error", error=f"{type(e).__name__}: {e}")
    finally:
        _update(run_id, finished_at=datetime.now(timezone.utc).isoformat())
        _crew_slot.release()


@app.post("/api/runs")
async def create_run(job_url: str = Form(...), resume: UploadFile = File(...)):
    job_url = job_url.strip()
    parsed = urlparse(job_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(400, "Enter a full job URL starting with http:// or https://")

    data = await resume.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(400, "Resume PDF must be 5 MB or smaller.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "The resume must be a PDF file.")
    try:
        text = _extract_pdf_text(data)
    except Exception:
        raise HTTPException(400, "Could not read that PDF. Is it password-protected or damaged?")
    if len(text) < MIN_RESUME_CHARS:
        raise HTTPException(
            400,
            "Almost no text could be read from that PDF. If it is a scanned image, "
            "export a text-based PDF from Word or Google Docs instead.",
        )

    if not _crew_slot.acquire(blocking=False):
        raise HTTPException(429, "Another analysis is already running. Try again when it finishes.")

    try:
        run_id = uuid.uuid4().hex[:12]
        out_dir = f"{RUNS_DIR}/{run_id}"
        (PROJECT_ROOT / out_dir).mkdir(parents=True, exist_ok=True)
        resume_path = PROJECT_ROOT / out_dir / "resume.md"
        resume_path.write_text(text, encoding="utf-8")

        with _runs_lock:
            _runs[run_id] = {
                "id": run_id,
                "job_url": job_url,
                "resume_name": resume.filename,
                "status": "queued",
                "step": 0,
                "results": {},
                "score": None,
                "error": None,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
            }

        threading.Thread(
            target=_run_crew, args=(run_id, job_url, str(resume_path), out_dir), daemon=True
        ).start()
    except Exception:
        _crew_slot.release()
        raise
    return {"run_id": run_id}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    with _runs_lock:
        run = _runs.get(run_id)
        if run is None:
            raise HTTPException(404, "Run not found (the server may have restarted).")
        return {**run, "results": dict(run["results"]), "steps": [s[2] for s in STEPS]}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


def main() -> None:
    import uvicorn

    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", "8000"))
    print(f"\n  Job Application Agents → http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
