from io import BytesIO

from langfuse.openai import openai
from pypdf import PdfReader

from app.schemas import ParsedResume

PROMPT_VERSION = "parse-v1"
MODEL = "gpt-4o-mini"  # placeholder — pin after feasibility spike

SYSTEM_PROMPT = (
    "You are a resume parser. Extract ONLY information explicitly present in "
    "the resume text below. Never infer, guess, or invent values that are not "
    "stated. If a field is not present, leave it null (or an empty list for "
    "list fields). Do not fabricate dates, companies, degrees, or skills that "
    "are not written in the source text."
)


def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def parse_resume(text: str) -> ParsedResume:
    response = openai.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format=ParsedResume,
        temperature=0,
        name="parse-resume",
    )
    return response.choices[0].message.parsed
