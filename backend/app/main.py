import uuid
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Command
from langgraph.checkpoint.postgres import PostgresSaver

import app.agents.graph as graph_module
from app.config import DATABASE_URL
from app.database import init_db, persist_meeting_results
from app.services.transcription import transcribe_audio

# psycopg connection string — strip the "+psycopg" SQLAlchemy driver prefix
_PG_CONN_STR = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create application tables (meetings, decisions, action_items, …)
    init_db()
    # 2. Open a long-lived psycopg connection for the LangGraph checkpointer,
    #    create the checkpoint tables once via .setup(), then swap the module-
    #    level graph to use PostgresSaver so approvals survive restarts.
    with PostgresSaver.from_conn_string(_PG_CONN_STR) as checkpointer:
        checkpointer.setup()
        graph_module.meeting_graph = graph_module.build_meeting_graph(checkpointer)
        yield
    # Connection closes automatically when the context manager exits on shutdown.


app = FastAPI(title="MeetOps AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranscriptRequest(BaseModel):
    transcript: str


class ResumeRequest(BaseModel):
    thread_id: str
    approval_decisions: Dict[str, str]  # {action_id: "approved" | "rejected"}


def _run_until_interrupt(transcript: str) -> dict:
    """Run the graph until the human-approval interrupt, then return the
    pending actions plus a thread_id the client uses to resume."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    result = graph_module.meeting_graph.invoke({"transcript": transcript}, config=config)

    interrupts = result.get("__interrupt__")
    if interrupts:
        return {
            "status": "awaiting_approval",
            "thread_id": thread_id,
            "meeting_title": result.get("meeting_title"),
            "executive_summary": result.get("executive_summary"),
            "key_points": result.get("key_points"),
            "decisions": result.get("decisions"),
            "risks_or_blockers": result.get("risks_or_blockers"),
            "approval_request": interrupts[0].value,
        }

    # No pending actions -> graph ran to completion in one pass.
    return {"status": "completed", "thread_id": thread_id, **result}


@app.get("/")
def root():
    return {"message": "MeetOps AI backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze")
def analyze_meeting(request: TranscriptRequest):
    return _run_until_interrupt(request.transcript)


@app.post("/resume")
def resume_meeting(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = graph_module.meeting_graph.invoke(
        Command(resume=request.approval_decisions), config=config
    )

    meeting_id = persist_meeting_results(
        transcript=result.get("transcript", ""),
        state=result,
    )

    return {
        "status": "completed",
        "thread_id": request.thread_id,
        "meeting_id": meeting_id,
        "meeting_title": result.get("meeting_title"),
        "executive_summary": result.get("executive_summary"),
        "key_points": result.get("key_points"),
        "decisions": result.get("decisions"),
        "action_items": result.get("action_items"),
        "risks_or_blockers": result.get("risks_or_blockers"),
        "calendar_suggestions": result.get("calendar_suggestions"),
        "follow_up_email": result.get("follow_up_email"),
        "executed_actions": result.get("executed_actions"),
        "audit_log": result.get("audit_log"),
        "final_report": result.get("final_report"),
    }


@app.post("/upload-transcript")
async def upload_transcript(file: UploadFile = File(...)):
    content = await file.read()
    return _run_until_interrupt(content.decode("utf-8"))


@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        transcript = transcribe_audio(tmp_path)
    finally:
        os.remove(tmp_path)

    response = _run_until_interrupt(transcript)
    response["transcript"] = transcript
    return response
