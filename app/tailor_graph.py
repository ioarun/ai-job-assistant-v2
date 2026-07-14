from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_sessionmaker
from app.models import TailorRun
from app.schemas import ParsedResume, TailoredResume
from app.tailor import tailor_resume, write_cover_letter


class TailorState(TypedDict):
    job_pick_id: int
    resume_id: int
    resume_text: str
    parsed: dict
    job_description: str
    tailored_resume: dict | None
    cover_letter: dict | None
    status: str  # "pending" | "awaiting_review" | "approved" | "revise"
    corrections: str | None


async def _get_latest_tailor_run(session: AsyncSession, job_pick_id: int) -> TailorRun:
    result = await session.execute(
        select(TailorRun)
        .where(TailorRun.job_pick_id == job_pick_id)
        .order_by(TailorRun.id.desc())
        .limit(1)
    )
    return result.scalar_one()


async def generate_resume_node(state: TailorState) -> dict:
    parsed = ParsedResume(**state["parsed"])
    tailored_resume = tailor_resume(
        state["resume_text"],
        parsed,
        state["job_description"],
        state.get("corrections"),
    )
    tailored_resume_dict = tailored_resume.model_dump()

    async with get_sessionmaker()() as session:
        tailor_run = await _get_latest_tailor_run(session, state["job_pick_id"])
        tailor_run.resume_content = tailored_resume_dict["content"]
        tailor_run.resume_emphasized_skills = tailored_resume_dict["emphasized_skills"]
        await session.commit()

    return {"tailored_resume": tailored_resume_dict}


async def generate_letter_node(state: TailorState) -> dict:
    parsed = ParsedResume(**state["parsed"])
    tailored_resume = TailoredResume(**state["tailored_resume"])
    cover_letter = write_cover_letter(
        state["resume_text"],
        parsed,
        state["job_description"],
        tailored_resume,
        state.get("corrections"),
    )
    cover_letter_dict = cover_letter.model_dump()

    async with get_sessionmaker()() as session:
        tailor_run = await _get_latest_tailor_run(session, state["job_pick_id"])
        tailor_run.cover_letter_content = cover_letter_dict["content"]
        tailor_run.cover_letter_emphasized_skills = cover_letter_dict[
            "emphasized_skills"
        ]
        tailor_run.status = "awaiting_review"
        await session.commit()

    return {"cover_letter": cover_letter_dict, "status": "awaiting_review"}


def review_node(state: TailorState) -> dict:
    decision = interrupt(
        {
            "tailored_resume": state["tailored_resume"],
            "cover_letter": state["cover_letter"],
        }
    )
    if decision["action"] == "approve":
        return {"status": "approved"}
    return {"status": "revise", "corrections": decision.get("corrections")}


def route_after_review(state: TailorState) -> str:
    return "persist_approved" if state["status"] == "approved" else "generate_resume"


async def persist_approved_node(state: TailorState) -> dict:
    async with get_sessionmaker()() as session:
        tailor_run = await _get_latest_tailor_run(session, state["job_pick_id"])
        tailor_run.status = "approved"
        await session.commit()
    return {}


def build_tailor_graph(checkpointer):
    graph = StateGraph(TailorState)
    graph.add_node("generate_resume", generate_resume_node)
    graph.add_node("generate_letter", generate_letter_node)
    graph.add_node("review", review_node)
    graph.add_node("persist_approved", persist_approved_node)

    graph.add_edge(START, "generate_resume")
    graph.add_edge("generate_resume", "generate_letter")
    graph.add_edge("generate_letter", "review")
    graph.add_conditional_edges("review", route_after_review)
    graph.add_edge("persist_approved", END)

    return graph.compile(checkpointer=checkpointer)
