from typing import Protocol

import httpx

from app.config import get_settings
from app.schemas import JobPosting


class JobSource(Protocol):
    def search(
        self, keywords: str, location: str | None = None
    ) -> list[JobPosting]: ...


class AdzunaJobSource:
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def search(self, keywords: str, location: str | None = None) -> list[JobPosting]:
        settings = get_settings()
        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_api_key,
            "results_per_page": 50,
            "what": keywords,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        url = f"{self.BASE_URL}/{settings.adzuna_country}/search/1"
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return [
            JobPosting(
                title=item.get("title", ""),
                company=(item.get("company") or {}).get("display_name"),
                location=(item.get("location") or {}).get("display_name"),
                description=item.get("description"),
                url=item.get("redirect_url"),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
            )
            for item in data.get("results", [])
        ]
