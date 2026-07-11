# ADR-0012: PDF ingestion via `pypdf` (local text extraction)

Status: Accepted
Date: 2026-07-06

## Context
Phase B (roadmap) begins with an **ingest** step: an uploaded resume **PDF** must be turned
into **raw text** before the OpenAI Structured-Outputs parse produces `ParsedResume`. We need
to choose *how* the bytes become text.

Two properties shape the choice:
- **PII enters the system here.** Resume text is personal data; the Responsible-AI stance
  (CLAUDE.md; hiring is high-risk under the EU AI Act / NYC LL144) favours keeping it **local**
  and shipping the minimum to any third party.
- **Evals need determinism.** The parse eval (eval-strategy §4) is only meaningful if the same
  PDF yields the same text every run, and if *ingest* failures can be told apart from *parse*
  failures — i.e. a clean seam between the two stages.

Real-world resumes are almost always **text-based** PDFs (exported from Word / Google Docs /
LaTeX), not scans, so a text-layer extractor covers the overwhelming majority of inputs.

## Decision
Use **`pypdf`** to extract text from uploaded PDFs, **in-process and page-by-page**, with no
external service. `extract_text()` (Phase B parse logic) reads each page and concatenates the
text; that text is the sole input to the LLM parse.

- Keep **ingest** and **parse** as separate, independently-evaluated stages.
- Extraction is **deterministic** (same bytes → same text), so eval runs are reproducible.
- Guard the output: treat **empty / below-min-length** extraction as an ingest failure and
  record it on the `ParseRun` row rather than sending near-empty text to the model.

## Alternatives considered
- **OCR (Tesseract / cloud OCR)** — required only for **scanned / image-only** PDFs; adds a
  heavy dependency (or a third-party call), is non-deterministic, and is unnecessary for the
  text-based resumes that dominate. **Rejected for MVP; kept as the fallback** when text
  extraction yields empty/garbage output.
- **Send the PDF straight to a vision-capable model** — handles scans and complex layout, but
  ships **full PII** to the provider, costs more per call, is less deterministic, and **blurs
  the eval** (ingest errors become indistinguishable from parse errors). **Rejected**; possible
  future fallback for hard layouts.

## Consequences
- (+) **Simple, local, cheap, deterministic**; PII stays on the box; a **clean ingest↔parse
  seam** lets each stage be evaluated on its own.
- (+) No new services or infra; one small dependency (`pypdf`).
- (−) **Fails on scanned / image-only PDFs**, and **multi-column layouts can garble reading
  order**. **Mitigation:** validate extracted text is non-empty / above a minimum length, flag
  low-yield extractions, and defer an **OCR / vision fallback** to a future ADR if real inputs
  demand it.

Feeds the Phase B `ParsedResume` parse (Structured Outputs, ADR-0010); OCR / vision-model
fallback deferred to a future ADR.
