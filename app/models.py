from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Resume(Base):
    __tablename__ = "resume"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parse_runs: Mapped[list["ParseRun"]] = relationship(back_populates="resume")
    job_picks: Mapped[list["JobPick"]] = relationship(back_populates="resume")


class ParseRun(Base):
    __tablename__ = "parse_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id"))
    status: Mapped[str]
    model: Mapped[str]
    prompt_version: Mapped[str]
    parsed: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    resume: Mapped["Resume"] = relationship(back_populates="parse_runs")

class JobPick(Base):
    __tablename__ = "job_pick"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resume.id"))
    title: Mapped[str]
    company: Mapped[str | None]
    location: Mapped[str | None]
    description: Mapped[str | None]
    url: Mapped[str | None]
    salary_min: Mapped[float | None]
    salary_max: Mapped[float | None]
    score: Mapped[int | None]
    reason: Mapped[str | None]
    picked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    resume: Mapped["Resume"] = relationship(back_populates="job_picks")

