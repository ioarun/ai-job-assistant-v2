from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from langfuse import get_client
from langfuse.openai import openai  # drop-in: same OpenAI API, auto-traced
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.graph import build_graph
from app.models import ParseRun, Resume
from app.parse import MODEL, PROMPT_VERSION


@asynccontextmanager
async def lifespan(app: FastAPI):
    psycopg_url = get_settings().database_url.replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    async with AsyncPostgresSaver.from_conn_string(psycopg_url) as checkpointer:
        await checkpointer.setup()
        app.state.graph = build_graph(checkpointer)
        yield


app = FastAPI(lifespan=lifespan)


def _graph_result_to_response(result: dict) -> dict:
    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        return {"status": "awaiting_review", "parsed": payload["parsed"]}
    return {"status": result.get("status"), "parsed": result.get("parsed")}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/resumes")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_bytes = await file.read()

    resume = Resume(filename=file.filename)
    db.add(resume)
    await db.flush()

    parse_run = ParseRun(
        resume_id=resume.id,
        status="pending",
        model=MODEL,
        prompt_version=PROMPT_VERSION,
        parsed=None,
        error=None,
    )
    db.add(parse_run)
    await db.commit()

    config = {"configurable": {"thread_id": str(resume.id)}}
    try:
        result = await app.state.graph.ainvoke(
            {
                "resume_id": resume.id,
                "pdf_bytes": pdf_bytes,
                "text": "",
                "parsed": None,
                "status": "pending",
                "corrections": None,
            },
            config=config,
        )
    except Exception as e:
        parse_run.status = "failed"
        parse_run.error = str(e)
        await db.commit()
        raise HTTPException(status_code=422, detail=str(e)) from e

    return {"resume_id": resume.id, **_graph_result_to_response(result)}


@app.get("/resumes/{resume_id}/parse")
async def get_parse(resume_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ParseRun)
        .where(ParseRun.resume_id == resume_id)
        .order_by(ParseRun.id.desc())
        .limit(1)
    )
    parse_run = result.scalar_one_or_none()
    if parse_run is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"status": parse_run.status, "parsed": parse_run.parsed}


class CorrectionsRequest(BaseModel):
    corrections: str


@app.post("/resumes/{resume_id}/parse/approve")
async def approve_parse(resume_id: int):
    config = {"configurable": {"thread_id": str(resume_id)}}
    result = await app.state.graph.ainvoke(
        Command(resume={"action": "approve"}), config=config
    )
    return {"resume_id": resume_id, **_graph_result_to_response(result)}


@app.post("/resumes/{resume_id}/parse/corrections")
async def submit_corrections(resume_id: int, body: CorrectionsRequest):
    config = {"configurable": {"thread_id": str(resume_id)}}
    result = await app.state.graph.ainvoke(
        Command(resume={"action": "revise", "corrections": body.corrections}),
        config=config,
    )
    return {"resume_id": resume_id, **_graph_result_to_response(result)}


@app.get("/hello")
def hello():
    response = openai.chat.completions.create(
        model="gpt-4o-mini",   # placeholder — pin the real model before Phase B
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        name="hello-phase-a",  # labels the trace in Langfuse
    )
    get_client().flush()       # force-send the trace before returning (demo-only)
    return {"message": response.choices[0].message.content}
