from __future__ import annotations

import json
import logging
from pathlib import Path

from .changelog import append_draft
from .config import Settings
from .github import GitHubClient


def run() -> int:
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    event = json.loads(Path(settings.event_path).read_text(encoding="utf-8"))
    pull = event["pull_request"]
    if not pull.get("merged"):
        return 0
    client = GitHubClient(settings.token, settings.repository, settings.api_url)
    labels = client.issue_labels(int(pull["number"]))
    append_draft(client, pull, labels)
    logging.info("draft changelog entry created")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
