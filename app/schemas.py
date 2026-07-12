from pydantic import BaseModel


class WorkEntry(BaseModel):
    title: str | None = None
    company: str | None = None
    start: str | None = None
    end: str | None = None
    highlights: list[str] = []


class ProjectEntry(BaseModel):
    name: str | None = None
    url: str | None = None
    start: str | None = None
    end: str | None = None
    highlights: list[str] = []


class EducationEntry(BaseModel):
    degree: str | None = None
    institution: str | None = None
    start: str | None = None
    end: str | None = None


class ParsedResume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = []
    work_history: list[WorkEntry] = []
    projects: list[ProjectEntry] = []
    education: list[EducationEntry] = []
