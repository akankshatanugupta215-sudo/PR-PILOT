from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
VALID_CATEGORIES = {"bug", "security", "style", "documentation", "tests", "enhancement"}


@dataclass(frozen=True)
class Finding:
    severity: str
    filename: str
    line: int
    explanation: str
    suggested_fix: str
    category: str = "bug"
    confidence: float = 0.0
    heuristic: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Finding":
        severity = str(value.get("severity", "")).lower()
        category = str(value.get("category", "bug")).lower()
        filename = str(value.get("filename", ""))
        explanation = str(value.get("explanation", "")).strip()
        fix = str(value.get("suggested_fix", "")).strip()
        try:
            line = int(value.get("line"))
            confidence = float(value.get("confidence", 0.0))
        except (TypeError, ValueError) as exc:
            raise ValueError("line and confidence must be numbers") from exc
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"invalid severity: {severity}")
        if category not in VALID_CATEGORIES:
            raise ValueError(f"invalid category: {category}")
        if not filename or filename.startswith("/") or ".." in filename.split("/"):
            raise ValueError("invalid filename")
        if line < 1 or not explanation or not fix:
            raise ValueError("finding needs a positive line, explanation, and suggested_fix")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return cls(severity, filename, line, explanation, fix, category, confidence, bool(value.get("heuristic", False)))


@dataclass
class Analysis:
    findings: list[Finding] = field(default_factory=list)
    summary: str = ""
    test_warning: str | None = None
    documentation_warning: str | None = None
