from langfuse.openai import openai

from app.schemas import GapReport, ParsedResume

PROMPT_VERSION = "gap-v1"
MODEL = "gpt-4o-mini"  # placeholder — pin after feasibility spike

SYSTEM_PROMPT = (
    "You are a career-fit analyst. Compare the candidate's structured resume against "
    "the job description and produce an honest gap report. match_score is 0-100. "
    "matched_skills are skills or experience genuinely present in the resume that "
    "satisfy the job's requirements. missing_skills are requirements from the job "
    "description that the resume does not demonstrate. Ground everything in the "
    "resume and job description text — never invent skills or requirements not "
    "present in either. This analysis is advisory only, not a pass/fail judgment "
    "of the candidate."
)


def analyze_gap(resume: ParsedResume, job_description: str) -> GapReport:
    user_content = (
        f"RESUME:\n{resume.model_dump_json()}\n\n"
        f"JOB DESCRIPTION:\n{job_description}"
    )

    response = openai.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format=GapReport,
        temperature=0,
        name="analyze-gap",
    )
    return response.choices[0].message.parsed
