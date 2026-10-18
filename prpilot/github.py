"""Small GitHub REST client with bounded retries for transient failures."""
from __future__ import annotations

import json
import logging
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOG = logging.getLogger(__name__)


class GitHubError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class GitHubClient:
    def __init__(self, token: str, repository: str, api_url: str = "https://api.github.com", retries: int = 3, sleep=time.sleep):
        if not token or not repository or "/" not in repository:
            raise ValueError("GITHUB_TOKEN and owner/repository are required")
        self.token, self.repository, self.api_url = token, repository, api_url.rstrip("/")
        self.retries, self.sleep = retries, sleep

    def request(self, method: str, path: str, payload: dict | None = None) -> Any:
        url = f"{self.api_url}{path}"
        body = json.dumps(payload).encode() if payload is not None else None
        for attempt in range(self.retries + 1):
            request = Request(url, data=body, method=method, headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "prpilot",
                "Content-Type": "application/json",
            })
            try:
                with urlopen(request, timeout=30) as response:
                    raw = response.read().decode()
                    return json.loads(raw) if raw else None
            except HTTPError as exc:
                transient = exc.code in {429, 500, 502, 503, 504}
                if not transient or attempt == self.retries:
                    detail = exc.read().decode(errors="replace")[:500]
                    raise GitHubError(f"GitHub {method} {path} failed ({exc.code}): {detail}", exc.code) from exc
            except URLError as exc:
                if attempt == self.retries:
                    raise GitHubError(f"GitHub request failed: {exc.reason}") from exc
            delay = min(2**attempt, 8)
            LOG.warning("transient GitHub error; retrying in %ss (%s/%s)", delay, attempt + 1, self.retries)
            self.sleep(delay)
        raise AssertionError("unreachable")

    def pull(self, number: int) -> dict:
        return self.request("GET", f"/repos/{self.repository}/pulls/{number}")

    def files(self, number: int) -> list[dict]:
        result: list[dict] = []
        page = 1
        while True:
            chunk = self.request("GET", f"/repos/{self.repository}/pulls/{number}/files?{urlencode({'per_page': 100, 'page': page})}")
            result.extend(chunk)
            if len(chunk) < 100:
                return result
            page += 1

    def reviews(self, number: int) -> list[dict]:
        return self.request("GET", f"/repos/{self.repository}/pulls/{number}/reviews?per_page=100")

    def create_review(self, number: int, body: str, comments: list[dict]) -> Any:
        return self.request("POST", f"/repos/{self.repository}/pulls/{number}/reviews", {"body": body, "event": "COMMENT", "comments": comments})

    def issue_labels(self, number: int) -> list[str]:
        labels = self.request("GET", f"/repos/{self.repository}/issues/{number}/labels?per_page=100")
        return [str(label["name"]) for label in labels]

    def repository_labels(self) -> list[str]:
        names: list[str] = []
        page = 1
        while True:
            labels = self.request("GET", f"/repos/{self.repository}/labels?{urlencode({'per_page': 100, 'page': page})}")
            names.extend(str(label["name"]) for label in labels)
            if len(labels) < 100:
                return names
            page += 1

    def add_labels(self, number: int, labels: list[str]) -> Any:
        return self.request("POST", f"/repos/{self.repository}/issues/{number}/labels", {"labels": labels})

    def contents(self, path: str, ref: str) -> dict:
        return self.request("GET", f"/repos/{self.repository}/contents/{path}?{urlencode({'ref': ref})}")
