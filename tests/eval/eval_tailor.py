"""Minimal tailoring eval — run manually (real OpenAI calls, not part of
`pytest`/CI):

    uv run --env-file .env python -m tests.eval.eval_tailor

Scores app.tailor.generate_tailored_docs() against every tailor_* fixture
quad in fixtures/ (`tailor_N_resume_text.txt` + `tailor_N_resume.json` +
`tailor_N_job.txt` + `tailor_N_expected.json`): code-based skill coverage on
the tailored resume, and a hard zero-fabrication gate via a narrowly-scoped
coded LLM-judge comparing generated text against the source resume.
"""

import json
import sys
from pathlib import Path

from langfuse import get_client
from langfuse.openai import openai
from pydantic import BaseModel

from app.schemas import ParsedResume, TailorResult
from app.tailor import generate_tailored_docs
from tests.eval.eval_parse import normalize

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ACCURACY_BAR = 0.80
JUDGE_MODEL = "gpt-4o-mini"

FABRICATION_JUDGE_PROMPT = (
    "You are a fact-checker comparing a generated resume or cover letter against "
    "the candidate's real source resume. List every claim in GENERATED TEXT — a "
    "skill, employer, title, date, achievement, or metric — that is NOT directly "
    "supported by, or that contradicts, SOURCE RESUME. Paraphrasing, reordering, "
    "condensing, or summarizing real content is NOT fabrication and must not be "
    "listed. If there are no fabricated claims, return an empty list."
)


class FabricationVerdict(BaseModel):
    fabricated_claims: list[str]


def judge_fabrication(
    source_resume_text: str, generated_content: str
) -> FabricationVerdict:
    response = openai.chat.completions.parse(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": FABRICATION_JUDGE_PROMPT},
            {
                "role": "user",
                "content": (
                    f"SOURCE RESUME:\n{source_resume_text}\n\n"
                    f"GENERATED TEXT:\n{generated_content}"
                ),
            },
        ],
        response_format=FabricationVerdict,
        temperature=0,
        name="judge-fabrication",
    )
    return response.choices[0].message.parsed


def skill_coverage(result: TailorResult, has_skills: list[str]) -> float:
    if not has_skills:
        return 1.0
    content = normalize(result.tailored_resume.content)
    emphasized = {normalize(s) for s in result.tailored_resume.emphasized_skills}
    covered = sum(
        1 for s in has_skills if normalize(s) in emphasized or normalize(s) in content
    )
    return covered / len(has_skills)


def score_fixture(
    name: str,
    resume_text: str,
    parsed: ParsedResume,
    job_description: str,
    has_skills: list[str],
) -> dict:
    result = generate_tailored_docs(resume_text, parsed, job_description)

    coverage = skill_coverage(result, has_skills)

    resume_verdict = judge_fabrication(resume_text, result.tailored_resume.content)
    letter_verdict = judge_fabrication(resume_text, result.cover_letter.content)
    fabricated_claims = (
        resume_verdict.fabricated_claims + letter_verdict.fabricated_claims
    )

    return {
        "name": name,
        "coverage": coverage,
        "fabricated": len(fabricated_claims),
        "fabricated_claims": fabricated_claims,
    }


def discover_fixtures() -> list[tuple[str, Path, Path, Path, Path]]:
    fixtures = []
    for resume_text_path in sorted(FIXTURES_DIR.glob("tailor_*_resume_text.txt")):
        base = resume_text_path.stem.removesuffix("_resume_text")
        resume_json_path = FIXTURES_DIR / f"{base}_resume.json"
        job_path = FIXTURES_DIR / f"{base}_job.txt"
        expected_path = FIXTURES_DIR / f"{base}_expected.json"
        if not (
            resume_json_path.exists() and job_path.exists() and expected_path.exists()
        ):
            continue
        fixtures.append(
            (base, resume_text_path, resume_json_path, job_path, expected_path)
        )
    return fixtures


def main() -> int:
    results = []
    for name, resume_text_path, resume_json_path, job_path, expected_path in (
        discover_fixtures()
    ):
        resume_text = resume_text_path.read_text()
        parsed = ParsedResume(**json.loads(resume_json_path.read_text()))
        job_description = job_path.read_text()
        expected = json.loads(expected_path.read_text())
        results.append(
            score_fixture(
                name, resume_text, parsed, job_description, expected["has_skills"]
            )
        )

    get_client().flush()  # force traces out now, for immediate Langfuse visibility

    print("--- Tailor eval report ---")
    for r in results:
        print(
            f"[{r['name']}] coverage={r['coverage']:.2%} fabricated={r['fabricated']}"
        )
        for claim in r["fabricated_claims"]:
            print(f"    - {claim}")

    mean_coverage = sum(r["coverage"] for r in results) / len(results)
    total_fabricated = sum(r["fabricated"] for r in results)

    print(f"\nFixtures scored: {len(results)}")
    print(f"Mean coverage: {mean_coverage:.2%} (bar: {ACCURACY_BAR:.0%})")
    print(f"Total fabricated claims: {total_fabricated}")

    coverage_pass = mean_coverage >= ACCURACY_BAR
    fabrication_pass = total_fabricated == 0
    print(f"Coverage bar: {'PASS' if coverage_pass else 'FAIL'}")
    print(f"Fabrication gate: {'PASS' if fabrication_pass else 'FAIL'}")

    return 0 if fabrication_pass else 1


if __name__ == "__main__":
    sys.exit(main())
