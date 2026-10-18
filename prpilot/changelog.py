from __future__ import annotations

import base64
from datetime import date

from .github import GitHubClient, GitHubError


def classify(labels: list[str], title: str) -> str:
    names = {label.lower() for label in labels}
    text = title.lower()
    if "bug" in names or "fix" in names or text.startswith(("fix", "bugfix")):
        return "Fixes"
    if "enhancement" in names or "feature" in names or text.startswith(("feat", "feature")):
        return "Features"
    return "Maintenance"


def markdown_entry(number: int, title: str, author: str) -> str:
    return f"- {title} (#{number}) by @{author}"


def draft_section(pull: dict, labels: list[str], today: date | None = None) -> str:
    when = (today or date.today()).isoformat()
    group = classify(labels, str(pull.get("title", "")))
    entry = markdown_entry(int(pull["number"]), str(pull["title"]), str(pull["user"]["login"]))
    return f"## {when}\n\n### {group}\n\n{entry}\n"


def append_draft(client: GitHubClient, pull: dict, labels: list[str], path: str = "CHANGELOG.draft.md") -> None:
    """Commit a draft only after a human-approved environment runs this workflow."""
    head = pull["base"]["sha"]
    try:
        current = client.contents(path, head)
        existing = base64.b64decode(current["content"]).decode()
        sha = current["sha"]
    except GitHubError as exc:
        if exc.status != 404:
            raise
        existing, sha = "# Draft changelog\n\n", None
    content = existing.rstrip() + "\n\n" + draft_section(pull, labels)
    payload = {"message": f"docs: draft changelog for #{pull['number']}", "content": base64.b64encode(content.encode()).decode(), "branch": pull["base"]["ref"]}
    if sha:
        payload["sha"] = sha
    client.request("PUT", f"/repos/{client.repository}/contents/{path}", payload)
