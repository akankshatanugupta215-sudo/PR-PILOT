"""CLI entry point used by GitHub Actions; it never checks out or executes PR code."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import Settings
from .diff import file_name_groups, validate_findings
from .gemini import analyze
from .github import GitHubClient, GitHubError
from .models import Analysis, Finding

LOG = logging.getLogger(__name__)
MARKER = "<!-- prpilot:"


def labels_for(findings: list[Finding], groups: dict[str, list[str]]) -> list[str]:
    labels = {f.category for f in findings if f.category in {"bug", "security", "enhancement"}}
    if groups.get("tests"):
        labels.add("tests")
    if groups.get("documentation"):
        labels.add("documentation")
    return sorted(labels)


def heuristic_warnings(files: list[dict], groups: dict[str, list[str]]) -> tuple[str | None, str | None]:
    source = [str(f.get("filename", "")) for f in files if str(f.get("filename", "")).endswith((".py", ".js", ".ts", ".java", ".go", ".rb"))]
    tests = None if not source or groups.get("tests") else "Heuristic warning: source-code changes have no changed test file. This is not a verified failure."
    docs = None if not source or groups.get("documentation") else "Heuristic warning: source-code changes have no changed documentation file. This is not a verified failure."
    return tests, docs


def comment_body(finding: Finding) -> str:
    return f"**PRPilot {finding.severity.upper()} — {finding.category}**\n\n{finding.explanation}\n\n**Suggested fix:** {finding.suggested_fix}\n\n{MARKER}{finding.filename}:{finding.line}:{finding.severity} -->"


def review_body(analysis: Analysis, rejected: list[str]) -> str:
    lines = ["## PRPilot review", analysis.summary or "Automated review completed.", "<!-- prpilot:review -->"]
    if analysis.test_warning:
        lines.append(analysis.test_warning)
    if analysis.documentation_warning:
        lines.append(analysis.documentation_warning)
    if rejected:
        lines.append(f"{len(rejected)} AI finding(s) were withheld because their locations were not valid changed lines.")
    lines.append("AI findings are advisory and require human judgment.")
    return "\n\n".join(lines)


def already_reviewed(reviews: list[dict], head_sha: str) -> bool:
    return any(r.get("user", {}).get("login") == "github-actions[bot]" and MARKER in str(r.get("body", "")) and r.get("commit_id") == head_sha for r in reviews)


def run() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_env()
    event = json.loads(Path(settings.event_path).read_text(encoding="utf-8"))
    if event.get("pull_request", {}).get("head", {}).get("repo") is None:
        LOG.warning("PR head repository was deleted; skipping")
        return 0
    number = int(event["pull_request"]["number"])
    client = GitHubClient(settings.token, settings.repository, settings.api_url)
    pull = client.pull(number)
    if already_reviewed(client.reviews(number), pull["head"]["sha"]):
        LOG.info("review for this commit already exists; skipping duplicate")
        return 0
    files = client.files(number)
    groups = file_name_groups(files)
    if not settings.gemini_key:
        head_repo = str(event["pull_request"]["head"]["repo"].get("full_name", ""))
        if head_repo.lower() != settings.repository.lower():
            LOG.warning("GEMINI_API_KEY unavailable for fork PR; skipping AI review safely")
            return 0
        raise ValueError("GEMINI_API_KEY is missing for an in-repository pull request")
    analysis = analyze(settings.gemini_key, settings.gemini_model, pull, files)
    analysis.findings, rejected = validate_findings(analysis.findings, files)
    analysis.test_warning, analysis.documentation_warning = heuristic_warnings(files, groups)
    comments = [{"path": f.filename, "line": f.line, "side": "RIGHT", "body": comment_body(f)} for f in analysis.findings]
    client.create_review(number, review_body(analysis, rejected), comments)
    intended = labels_for(analysis.findings, groups)
    existing = set(client.issue_labels(number))
    # Only apply labels that are approved *and already exist* in this repository.
    # This avoids silently creating a new label through automation or failing on a typo.
    available = set(client.repository_labels())
    approved = [label for label in intended if label in {"bug", "enhancement", "documentation", "tests", "security"} and label in available and label not in existing]
    if approved:
        client.add_labels(number, approved)
    LOG.info("posted %s validated inline comment(s); withheld %s", len(comments), len(rejected))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        logging.exception("PRPilot failed: %s", exc)
        raise SystemExit(1)
