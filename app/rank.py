from langfuse.openai import openai

from app.schemas import JobPosting, JobRankingResult, ParsedResume, RankedJob

PROMPT_VERSION = "rank-v1"
MODEL = "gpt-4o-mini"  # placeholder — pin after feasibility spike

SYSTEM_PROMPT = (
    "You are a job-fit scorer. Given a candidate's structured resume and a list "
    "of job postings, score each job's fit for this candidate from 0 to 100. "
    "Ground every reason in specifics from the job description and the resume "
    "— never invent skills, experience, or requirements not present in either. "
    "Weigh seniority and scope, not just skill/topic overlap: if a posting clearly "
    "calls for substantially more experience, leadership, or ownership than the "
    "candidate's resume demonstrates (e.g. 'Staff', 'Principal', 'lead the "
    "architecture end-to-end', 'own the stack'), score it noticeably lower even if "
    "the technical domain matches well. Score every job in the list, using its index."
)


def rank_jobs(resume: ParsedResume, jobs: list[JobPosting]) -> list[RankedJob]:
    if not jobs:
        return []

    jobs_text = "\n\n".join(
        f"[{i}] {job.title} at {job.company or 'Unknown'}\n{job.description or ''}"
        for i, job in enumerate(jobs)
    )
    user_content = f"RESUME:\n{resume.model_dump_json()}\n\nJOB LISTINGS:\n{jobs_text}"

    response = openai.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format=JobRankingResult,
        temperature=0,
        name="rank-jobs",
    )
    result = response.choices[0].message.parsed

    scored = [
        RankedJob(job=jobs[s.job_index], score=s.score, reason=s.reason)
        for s in result.scores
        if 0 <= s.job_index < len(jobs)
    ]
    return sorted(scored, key=lambda r: r.score, reverse=True)
