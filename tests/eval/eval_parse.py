"""Minimal parse eval — run manually (real OpenAI call, not part of `pytest`/CI):

    uv run --env-file .env python tests/eval/eval_parse.py

Scores app.parse.parse_resume() against one synthetic, ground-truth fixture:
normalized exact match on scalar fields, precision/recall on skills, per-entry
match on work history / education, and a hard zero-fabrication gate on skills
(every extracted skill must appear verbatim in the source text — the base
strict-matching approach; semantic/RAG-augmented checking is deferred to B2).
"""

import sys
from pathlib import Path

from app.parse import parse_resume
from app.schemas import ParsedResume

FIXTURE_TEXT = (Path(__file__).parent / "fixtures" / "sample_resume_1.txt").read_text()

EXPECTED = {
    "name": "Jordan Lee",
    "email": "jordan.lee@example.com",
    "phone": "+1-555-0100",
    "skills": {"python", "sql", "docker"},
    "work_history": [
        {
            "title": "software engineer",
            "company": "acme corp",
            "start": "jan 2021",
            "end": "dec 2023",
        }
    ],
    "education": [
        {
            "degree": "b.s. computer science",
            "institution": "state university",
            "start": "2016",
            "end": "2020",
        }
    ],
}

ACCURACY_BAR = 0.95


def normalize(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.strip().lower().split())


def scalar_field_accuracy(parsed: ParsedResume) -> tuple[int, int]:
    fields = ["name", "email", "phone"]
    correct = sum(
        1
        for field in fields
        if normalize(getattr(parsed, field)) == normalize(EXPECTED[field])
    )
    return correct, len(fields)


def skills_precision_recall(parsed: ParsedResume) -> tuple[float, float]:
    predicted = {normalize(s) for s in parsed.skills}
    expected = EXPECTED["skills"]
    if not predicted:
        return 0.0, 0.0
    overlap = predicted & expected
    precision = len(overlap) / len(predicted)
    recall = len(overlap) / len(expected)
    return precision, recall


def entry_match_rate(
    predicted_entries: list, expected_entries: list, fields: list[str]
) -> tuple[int, int]:
    matched = 0
    for expected in expected_entries:
        for actual in predicted_entries:
            actual_tuple = tuple(normalize(getattr(actual, f, None)) for f in fields)
            expected_tuple = tuple(expected[f] for f in fields)
            if actual_tuple == expected_tuple:
                matched += 1
                break
    return matched, len(expected_entries)


def fabrication_count(parsed: ParsedResume, source_text: str) -> int:
    source_lower = source_text.lower()
    return sum(1 for skill in parsed.skills if skill.lower() not in source_lower)


def main() -> int:
    parsed = parse_resume(FIXTURE_TEXT)

    scalar_correct, scalar_total = scalar_field_accuracy(parsed)
    skills_precision, skills_recall = skills_precision_recall(parsed)
    work_fields = ["title", "company", "start", "end"]
    work_matched, work_total = entry_match_rate(
        parsed.work_history, EXPECTED["work_history"], work_fields
    )
    edu_fields = ["degree", "institution", "start", "end"]
    edu_matched, edu_total = entry_match_rate(
        parsed.education, EXPECTED["education"], edu_fields
    )
    fabricated = fabrication_count(parsed, FIXTURE_TEXT)

    scores = [
        scalar_correct / scalar_total,
        skills_precision,
        skills_recall,
        work_matched / work_total,
        edu_matched / edu_total,
    ]
    overall_accuracy = sum(scores) / len(scores)

    print("--- Parse eval report ---")
    print(f"Scalar fields (name/email/phone): {scalar_correct}/{scalar_total}")
    print(f"Skills precision: {skills_precision:.2f}  recall: {skills_recall:.2f}")
    print(f"Work history matched: {work_matched}/{work_total}")
    print(f"Education matched: {edu_matched}/{edu_total}")
    print(f"Fabricated skills: {fabricated}")
    print(f"Overall accuracy: {overall_accuracy:.2%} (bar: {ACCURACY_BAR:.0%})")

    accuracy_pass = overall_accuracy >= ACCURACY_BAR
    fabrication_pass = fabricated == 0
    print(f"Accuracy bar: {'PASS' if accuracy_pass else 'FAIL'}")
    print(f"Fabrication gate: {'PASS' if fabrication_pass else 'FAIL'}")

    return 0 if fabrication_pass else 1


if __name__ == "__main__":
    sys.exit(main())
