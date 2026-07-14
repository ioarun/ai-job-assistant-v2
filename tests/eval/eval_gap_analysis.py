"""Minimal gap-analysis eval — run manually (real OpenAI calls, not part of
`pytest`/CI):

    uv run --env-file .env python -m tests.eval.eval_gap_analysis

Scores app.gap_analysis.analyze_gap() against every gap_* fixture trio in
fixtures/ (`gap_N_resume.json` + `gap_N_job.txt` + `gap_N_expected.json`):
set precision/recall on matched_skills and missing_skills, and a hard
zero-fabrication gate (every matched_skill must be groundable in the resume;
every missing_skill must be groundable in the job description text).
"""

import json
import sys
from pathlib import Path

from langfuse import get_client

from app.gap_analysis import analyze_gap
from app.schemas import GapReport, ParsedResume
from tests.eval.eval_parse import normalize

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ACCURACY_BAR = 0.80


def skills_set_precision_recall(
    predicted: list[str], expected: list[str]
) -> tuple[float, float]:
    predicted_set = {normalize(s) for s in predicted}
    expected_set = {normalize(s) for s in expected}
    if not predicted_set:
        return 0.0, 0.0
    overlap = predicted_set & expected_set
    precision = len(overlap) / len(predicted_set)
    recall = len(overlap) / len(expected_set)
    return precision, recall


def fabrication_count(
    report: GapReport, resume: ParsedResume, job_description: str
) -> int:
    resume_text = resume.model_dump_json().lower()
    job_text = job_description.lower()
    matched_fabricated = sum(
        1 for skill in report.matched_skills if skill.lower() not in resume_text
    )
    missing_fabricated = sum(
        1 for skill in report.missing_skills if skill.lower() not in job_text
    )
    return matched_fabricated + missing_fabricated


def score_fixture(
    name: str, resume: ParsedResume, job_description: str, expected: dict
) -> dict:
    report = analyze_gap(resume, job_description)

    matched_precision, matched_recall = skills_set_precision_recall(
        report.matched_skills, expected["matched_skills"]
    )
    missing_precision, missing_recall = skills_set_precision_recall(
        report.missing_skills, expected["missing_skills"]
    )
    fabricated = fabrication_count(report, resume, job_description)

    scores = [matched_precision, matched_recall, missing_precision, missing_recall]
    overall_accuracy = sum(scores) / len(scores)

    return {
        "name": name,
        "matched_precision": matched_precision,
        "matched_recall": matched_recall,
        "missing_precision": missing_precision,
        "missing_recall": missing_recall,
        "fabricated": fabricated,
        "accuracy": overall_accuracy,
    }


def discover_fixtures() -> list[tuple[str, Path, Path, Path]]:
    fixtures = []
    for resume_path in sorted(FIXTURES_DIR.glob("gap_*_resume.json")):
        base = resume_path.stem.removesuffix("_resume")
        job_path = FIXTURES_DIR / f"{base}_job.txt"
        expected_path = FIXTURES_DIR / f"{base}_expected.json"
        if not job_path.exists() or not expected_path.exists():
            continue
        fixtures.append((base, resume_path, job_path, expected_path))
    return fixtures


def main() -> int:
    results = []
    for name, resume_path, job_path, expected_path in discover_fixtures():
        resume = ParsedResume(**json.loads(resume_path.read_text()))
        job_description = job_path.read_text()
        expected = json.loads(expected_path.read_text())
        results.append(score_fixture(name, resume, job_description, expected))

    get_client().flush()  # force traces out now, for immediate Langfuse visibility

    print("--- Gap analysis eval report ---")
    for r in results:
        print(
            f"[{r['name']}] matched_p={r['matched_precision']:.2f} "
            f"matched_r={r['matched_recall']:.2f} "
            f"missing_p={r['missing_precision']:.2f} "
            f"missing_r={r['missing_recall']:.2f} "
            f"fabricated={r['fabricated']} accuracy={r['accuracy']:.2%}"
        )

    overall_accuracy = sum(r["accuracy"] for r in results) / len(results)
    total_fabricated = sum(r["fabricated"] for r in results)

    print(f"\nFixtures scored: {len(results)}")
    print(f"Mean accuracy: {overall_accuracy:.2%} (bar: {ACCURACY_BAR:.0%})")
    print(f"Total fabricated skills: {total_fabricated}")

    accuracy_pass = overall_accuracy >= ACCURACY_BAR
    fabrication_pass = total_fabricated == 0
    print(f"Accuracy bar: {'PASS' if accuracy_pass else 'FAIL'}")
    print(f"Fabrication gate: {'PASS' if fabrication_pass else 'FAIL'}")

    return 0 if fabrication_pass else 1


if __name__ == "__main__":
    sys.exit(main())
