from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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
from app.job_source import AdzunaJobSource
from app.models import JobPick, ParseRun, Resume
from app.parse import MODEL, PROMPT_VERSION
from app.rank import rank_jobs
from app.schemas import ParsedResume, RankedJob


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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

class JobSearchRequest(BaseModel):
    resume_id: int
    keywords: str
    location: str | None = None


@app.post("/jobs/search")
async def search_jobs(body: JobSearchRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ParseRun)
        .where(ParseRun.resume_id == body.resume_id)
        .order_by(ParseRun.id.desc())
        .limit(1)
    )
    parse_run = result.scalar_one_or_none()
    if parse_run is None or parse_run.status != "approved":
        raise HTTPException(
            status_code=400, detail="Resume must be approved before job search"
        )

    resume = ParsedResume(**parse_run.parsed)
    jobs = AdzunaJobSource().search(body.keywords, body.location)
    ranked = rank_jobs(resume, jobs)

    return {"resume_id": body.resume_id, "jobs": [r.model_dump() for r in ranked]}


class JobPickRequest(BaseModel):
    resume_id: int
    picked: RankedJob


@app.post("/jobs/pick")
async def pick_job(body: JobPickRequest, db: AsyncSession = Depends(get_db)):
    job = body.picked.job
    job_pick = JobPick(
        resume_id=body.resume_id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        url=job.url,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        score=body.picked.score,
        reason=body.picked.reason,
    )
    db.add(job_pick)
    await db.commit()

    return {"resume_id": body.resume_id, "job_pick_id": job_pick.id}



@app.get("/hello")
def hello():
    response = openai.chat.completions.create(
        model="gpt-4o-mini",   # placeholder — pin the real model before Phase B
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        name="hello-phase-a",  # labels the trace in Langfuse
    )
    get_client().flush()       # force-send the trace before returning (demo-only)
    return {"message": response.choices[0].message.content}
