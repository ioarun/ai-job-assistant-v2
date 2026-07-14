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

class JobPosting(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None

class JobFitScore(BaseModel):
    job_index: int
    score: int
    reason: str

class JobRankingResult(BaseModel):
    scores: list[JobFitScore]


class RankedJob(BaseModel):
    job: JobPosting
    score: int
    reason: str


class GapReport(BaseModel):
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]


class TailoredResume(BaseModel):
    content: str
    emphasized_skills: list[str] = []


class CoverLetter(BaseModel):
    content: str
    emphasized_skills: list[str] = []


class TailorResult(BaseModel):
    tailored_resume: TailoredResume
    cover_letter: CoverLetter
