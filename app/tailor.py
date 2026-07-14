from langfuse.openai import openai

from app.schemas import CoverLetter, ParsedResume, TailoredResume, TailorResult

PROMPT_VERSION = "tailor-v1"
MODEL = "gpt-4o-mini"  # placeholder — pin after feasibility spike

GROUNDING_RULES = (
    "You may reorder, rephrase, condense, or emphasize existing content from the "
    "source resume to better match the job description. You must NOT invent "
    "employers, titles, dates, skills, technologies, achievements, or metrics that "
    "are not present in the source resume text. If the job description calls for "
    "something the resume does not show, do not add it — omission is always safer "
    "than embellishment. Every sentence you write must be traceable to a specific "
    "statement in the source resume text."
)

TAILOR_RESUME_SYSTEM_PROMPT = (
    "You are a resume editor helping a candidate tailor their resume to a specific "
    "job. Rewrite the resume as Markdown text that better emphasizes the parts of "
    "the candidate's real experience most relevant to the job description. "
    f"{GROUNDING_RULES} emphasized_skills must only contain strings copied verbatim "
    "from the candidate's parsed skills list — never introduce a skill name that "
    "isn't in that list."
)

COVER_LETTER_SYSTEM_PROMPT = (
    "You are a career writer helping a candidate write a cover letter for a "
    "specific job, consistent with their (already tailored) resume. Select 2-4 "
    "genuinely relevant experiences from the source resume and connect them to the "
    "job description's stated needs; do not restate the whole resume. "
    f"{GROUNDING_RULES} emphasized_skills must only contain strings copied verbatim "
    "from the candidate's parsed skills list — never introduce a skill name that "
    "isn't in that list."
)


def _with_corrections(content: str, corrections: str | None) -> str:
    if corrections:
        return f"{content}\n\n[Reviewer correction hints: {corrections}]"
    return content


def tailor_resume(
    resume_text: str,
    parsed: ParsedResume,
    job_description: str,
    corrections: str | None = None,
) -> TailoredResume:
    user_content = _with_corrections(
        f"SOURCE RESUME TEXT:\n{resume_text}\n\n"
        f"CANDIDATE SKILLS: {parsed.skills}\n\n"
        f"JOB DESCRIPTION:\n{job_description}",
        corrections,
    )

    response = openai.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": TAILOR_RESUME_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format=TailoredResume,
        temperature=0,
        name="tailor-resume",
    )
    return response.choices[0].message.parsed


def write_cover_letter(
    resume_text: str,
    parsed: ParsedResume,
    job_description: str,
    tailored_resume: TailoredResume,
    corrections: str | None = None,
) -> CoverLetter:
    user_content = _with_corrections(
        f"SOURCE RESUME TEXT:\n{resume_text}\n\n"
        f"CANDIDATE SKILLS: {parsed.skills}\n\n"
        f"TAILORED RESUME (already written for this job):\n"
        f"{tailored_resume.content}\n\n"
        f"JOB DESCRIPTION:\n{job_description}",
        corrections,
    )

    response = openai.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": COVER_LETTER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format=CoverLetter,
        temperature=0,
        name="write-cover-letter",
    )
    return response.choices[0].message.parsed


def generate_tailored_docs(
    resume_text: str,
    parsed: ParsedResume,
    job_description: str,
    corrections: str | None = None,
) -> TailorResult:
    tailored_resume = tailor_resume(resume_text, parsed, job_description, corrections)
    cover_letter = write_cover_letter(
        resume_text, parsed, job_description, tailored_resume, corrections
    )
    return TailorResult(tailored_resume=tailored_resume, cover_letter=cover_letter)
