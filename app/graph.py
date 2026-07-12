from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_sessionmaker
from app.models import ParseRun
from app.parse import extract_text, parse_resume


class ReviewState(TypedDict):
    resume_id: int
    pdf_bytes: bytes
    text: str
    parsed: dict | None
    status: str  # "pending" | "awaiting_review" | "approved" | "revise"
    corrections: str | None


async def _get_latest_parse_run(session: AsyncSession, resume_id: int) -> ParseRun:
    result = await session.execute(
        select(ParseRun)
        .where(ParseRun.resume_id == resume_id)
        .order_by(ParseRun.id.desc())
        .limit(1)
    )
    return result.scalar_one()


def ingest_node(state: ReviewState) -> dict:
    text = extract_text(state["pdf_bytes"])
    if len(text) < 50:
        raise ValueError("Extracted text is empty or too short")
    return {"text": text}


async def parse_node(state: ReviewState) -> dict:
    text = state["text"]
    if state.get("corrections"):
        text = f"{text}\n\n[Reviewer correction hints: {state['corrections']}]"
    parsed = parse_resume(text)
    parsed_dict = parsed.model_dump()

    async with get_sessionmaker()() as session:
        parse_run = await _get_latest_parse_run(session, state["resume_id"])
        parse_run.status = "awaiting_review"
        parse_run.parsed = parsed_dict
        await session.commit()

    return {"parsed": parsed_dict, "status": "awaiting_review"}


def review_node(state: ReviewState) -> dict:
    decision = interrupt({"parsed": state["parsed"]})
    if decision["action"] == "approve":
        return {"status": "approved"}
    return {"status": "revise", "corrections": decision.get("corrections")}


def route_after_review(state: ReviewState) -> str:
    return "persist_approved" if state["status"] == "approved" else "parse"


async def persist_approved_node(state: ReviewState) -> dict:
    async with get_sessionmaker()() as session:
        parse_run = await _get_latest_parse_run(session, state["resume_id"])
        parse_run.status = "approved"
        parse_run.parsed = state["parsed"]
        await session.commit()
    return {}


def build_graph(checkpointer):
    graph = StateGraph(ReviewState)
    graph.add_node("ingest", ingest_node)
    graph.add_node("parse", parse_node)
    graph.add_node("review", review_node)
    graph.add_node("persist_approved", persist_approved_node)

    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "parse")
    graph.add_edge("parse", "review")
    graph.add_conditional_edges("review", route_after_review)
    graph.add_edge("persist_approved", END)

    return graph.compile(checkpointer=checkpointer)
