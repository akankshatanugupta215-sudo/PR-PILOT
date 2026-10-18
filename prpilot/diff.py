"""Unified-diff parsing and strict GitHub inline-location validation."""
# Testing PRPilot automated review
# testing auto
from __future__ import annotations

import re
from collections import defaultdict

from .models import Finding

HUNK = re.compile(r"^@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")


def changed_right_lines(patch: str | None) -> set[int]:
    """Return only added/replaced destination lines that GitHub accepts as RIGHT comments."""
    if not patch:
        return set()
    lines: set[int] = set()
    new_line: int | None = None
    for raw in patch.splitlines():
        match = HUNK.match(raw)
        if match:
            new_line = int(match.group("new"))
            continue
        if new_line is None or raw.startswith("\\ No newline"):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            lines.add(new_line)
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_line += 1
    return lines


def changed_lines_by_file(files: list[dict]) -> dict[str, set[int]]:
    return {str(item["filename"]): changed_right_lines(item.get("patch")) for item in files if item.get("filename")}


def validate_findings(findings: list[Finding], files: list[dict]) -> tuple[list[Finding], list[str]]:
    locations = changed_lines_by_file(files)
    valid: list[Finding] = []
    rejected: list[str] = []
    for finding in findings:
        if finding.line in locations.get(finding.filename, set()):
            valid.append(finding)
        else:
            rejected.append(f"{finding.filename}:{finding.line} is not an added line in the fetched diff")
    return valid, rejected


def file_name_groups(files: list[dict]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for item in files:
        name = str(item.get("filename", ""))
        lower = name.lower()
        if lower.startswith(("test/", "tests/")) or "/test_" in lower or lower.endswith(("_test.py", ".test.js", ".spec.ts")):
            groups["tests"].append(name)
        if lower.startswith(("docs/", "doc/")) or lower.startswith("readme") or lower.endswith((".md", ".rst")):
            groups["documentation"].append(name)
    return dict(groups)
