from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from langfuse import get_client
from langfuse.openai import openai  # drop-in: same OpenAI API, auto-traced
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import ParseRun, Resume
from app.parse import MODEL, PROMPT_VERSION, extract_text, parse_resume

app = FastAPI()


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
    await db.flush()  # assigns resume.id without committing yet

    try:
        text = extract_text(pdf_bytes)
        if len(text) < 50:
            raise ValueError("Extracted text is empty or too short")
        parsed = parse_resume(text)
    except Exception as e:
        parse_run = ParseRun(
            resume_id=resume.id,
            status="failed",
            model=MODEL,
            prompt_version=PROMPT_VERSION,
            parsed=None,
            error=str(e),
        )
        db.add(parse_run)
        await db.commit()
        raise HTTPException(status_code=422, detail=str(e)) from e

    parse_run = ParseRun(
        resume_id=resume.id,
        status="success",
        model=MODEL,
        prompt_version=PROMPT_VERSION,
        parsed=parsed.model_dump(),
        error=None,
    )
    db.add(parse_run)
    await db.commit()

    return {
        "resume_id": resume.id,
        "parse_run_id": parse_run.id,
        "parsed": parsed.model_dump(),
    }


@app.get("/hello")
def hello():
    response = openai.chat.completions.create(
        model="gpt-4o-mini",   # placeholder — pin the real model before Phase B
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        name="hello-phase-a",  # labels the trace in Langfuse
    )
    get_client().flush()       # force-send the trace before returning (demo-only)
    return {"message": response.choices[0].message.content}
