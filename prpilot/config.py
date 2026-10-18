from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    token: str
    repository: str
    api_url: str
    event_path: str
    gemini_key: str
    gemini_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            token=os.environ.get("GITHUB_TOKEN", ""),
            repository=os.environ.get("GITHUB_REPOSITORY", ""),
            api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
            event_path=os.environ.get("GITHUB_EVENT_PATH", ""),
            gemini_key=os.environ.get("GEMINI_API_KEY", ""),
            # Verified against Google's official model catalog on 2026-10-18.
            gemini_model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
        )
