"""Minimal parse eval — run manually (real OpenAI calls, not part of `pytest`/CI):

    uv run --env-file .env python -m tests.eval.eval_parse

Scores app.parse.parse_resume() against every fixture pair in fixtures/
(`<name>.txt` + `<name>_expected.json`): normalized exact match on scalar
fields, precision/recall on skills, per-entry match on work history /
education, and a hard zero-fabrication gate on skills (every extracted skill
must appear verbatim in the source text — the base strict-matching approach;
semantic/RAG-augmented checking is deferred to B2).
"""

import json
import sys
from pathlib import Path

from langfuse import get_client

from app.parse import parse_resume
from app.schemas import ParsedResume

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ACCURACY_BAR = 0.95


def normalize(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.strip().lower().split())


def scalar_field_accuracy(parsed: ParsedResume, expected: dict) -> tuple[int, int]:
    fields = ["name", "email", "phone"]
    correct = sum(
        1
        for field in fields
        if normalize(getattr(parsed, field)) == normalize(expected[field])
    )
    return correct, len(fields)


def skills_precision_recall(
    parsed: ParsedResume, expected: dict
) -> tuple[float, float]:
    predicted = {normalize(s) for s in parsed.skills}
    expected_skills = {normalize(s) for s in expected["skills"]}
    if not predicted:
        return 0.0, 0.0
    overlap = predicted & expected_skills
    precision = len(overlap) / len(predicted)
    recall = len(overlap) / len(expected_skills)
    return precision, recall


def entry_match_rate(
    predicted_entries: list, expected_entries: list, fields: list[str]
) -> tuple[int, int]:
    matched = 0
    for expected in expected_entries:
        for actual in predicted_entries:
            actual_tuple = tuple(normalize(getattr(actual, f, None)) for f in fields)
            expected_tuple = tuple(normalize(expected[f]) for f in fields)
            if actual_tuple == expected_tuple:
                matched += 1
                break
    return matched, len(expected_entries)


def fabrication_count(parsed: ParsedResume, source_text: str) -> int:
    source_lower = source_text.lower()
    return sum(1 for skill in parsed.skills if skill.lower() not in source_lower)


def score_fixture(name: str, text: str, expected: dict) -> dict:
    parsed = parse_resume(text)

    scalar_correct, scalar_total = scalar_field_accuracy(parsed, expected)
    skills_precision, skills_recall = skills_precision_recall(parsed, expected)

    work_fields = ["title", "company", "start", "end"]
    work_matched, work_total = entry_match_rate(
        parsed.work_history, expected["work_history"], work_fields
    )
    edu_fields = ["degree", "institution", "start", "end"]
    edu_matched, edu_total = entry_match_rate(
        parsed.education, expected["education"], edu_fields
    )
    fabricated = fabrication_count(parsed, text)

    # Guard against zero-entry fixtures (e.g. no education section) so we
    # don't divide by zero — treat "expected none, got none" as a full match.
    work_score = (work_matched / work_total) if work_total else 1.0
    edu_score = (edu_matched / edu_total) if edu_total else 1.0

    scores = [
        scalar_correct / scalar_total,
        skills_precision,
        skills_recall,
        work_score,
        edu_score,
    ]
    overall_accuracy = sum(scores) / len(scores)

    return {
        "name": name,
        "scalar": f"{scalar_correct}/{scalar_total}",
        "skills_precision": skills_precision,
        "skills_recall": skills_recall,
        "work": f"{work_matched}/{work_total}",
        "education": f"{edu_matched}/{edu_total}",
        "fabricated": fabricated,
        "accuracy": overall_accuracy,
    }


def discover_fixtures() -> list[tuple[str, Path, Path]]:
    fixtures = []
    for text_path in sorted(FIXTURES_DIR.glob("*.txt")):
        expected_path = FIXTURES_DIR / f"{text_path.stem}_expected.json"
        if not expected_path.exists():
            continue
        fixtures.append((text_path.stem, text_path, expected_path))
    return fixtures


def main() -> int:
    results = []
    for name, text_path, expected_path in discover_fixtures():
        text = text_path.read_text()
        expected = json.loads(expected_path.read_text())
        results.append(score_fixture(name, text, expected))

    get_client().flush()  # force traces out now, for immediate Langfuse visibility

    print("--- Parse eval report ---")
    for r in results:
        print(
            f"[{r['name']}] scalar={r['scalar']} "
            f"skills_p={r['skills_precision']:.2f} skills_r={r['skills_recall']:.2f} "
            f"work={r['work']} education={r['education']} "
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
