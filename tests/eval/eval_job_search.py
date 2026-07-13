"""Job-relevance eval — precision@10 (eval-strategy §6). Run manually, interactively:

    uv run --env-file .env python -m tests.eval.eval_job_search \\
        <resume_id> <keywords> [location]

Runs a real search + LLM rerank (the same pipeline POST /jobs/search uses), shows the
top 10 results, and asks a human to label each relevant or not — matching
eval-strategy's "human (+ LLM-judge to scale)" primary grader for this stage. Live job
listings aren't static like the Phase B fixtures, so this can't run against a fixed
dataset the way eval_parse.py does; it grades a fresh search each time.
"""

import asyncio
import sys

from sqlalchemy import select

from app.db import get_sessionmaker
from app.job_source import AdzunaJobSource
from app.models import ParseRun
from app.rank import rank_jobs
from app.schemas import ParsedResume

PRECISION_AT_10_BAR = 0.70


async def get_approved_resume(resume_id: int) -> ParsedResume:
    async with get_sessionmaker()() as session:
        result = await session.execute(
            select(ParseRun)
            .where(ParseRun.resume_id == resume_id, ParseRun.status == "approved")
            .order_by(ParseRun.id.desc())
            .limit(1)
        )
        parse_run = result.scalar_one()
        return ParsedResume(**parse_run.parsed)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: eval_job_search.py <resume_id> <keywords> [location]")
        return 1

    resume_id = int(sys.argv[1])
    keywords = sys.argv[2]
    location = sys.argv[3] if len(sys.argv) > 3 else None

    resume = asyncio.run(get_approved_resume(resume_id))
    jobs = AdzunaJobSource().search(keywords, location)
    ranked = rank_jobs(resume, jobs)[:10]

    print(f"--- Top {len(ranked)} results for '{keywords}' ---\n")
    labels = []
    for i, r in enumerate(ranked, start=1):
        print(f"[{i}] {r.job.title} — {r.job.company} (score {r.score})")
        print(f"    {r.reason}")
        answer = input("    Relevant? (y/n): ").strip().lower()
        labels.append(answer == "y")
        print()

    relevant_count = sum(labels)
    total = len(labels)
    precision = relevant_count / total if total else 0.0

    print(
        f"--- Precision@10: {relevant_count}/{total} = {precision:.0%} "
        f"(bar: {PRECISION_AT_10_BAR:.0%}) ---"
    )
    print("PASS" if precision >= PRECISION_AT_10_BAR else "FAIL")

    return 0 if precision >= PRECISION_AT_10_BAR else 1


if __name__ == "__main__":
    sys.exit(main())
