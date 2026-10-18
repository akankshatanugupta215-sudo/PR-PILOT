from datetime import date

from prpilot.changelog import classify, draft_section


def test_changelog_groups_features_fixes_and_maintenance():
    assert classify(["enhancement"], "anything") == "Features"
    assert classify(["bug"], "anything") == "Fixes"
    assert classify([], "chore: cleanup") == "Maintenance"


def test_draft_section_has_traceable_entry():
    pull = {"number": 42, "title": "feat: search", "user": {"login": "ada"}}
    result = draft_section(pull, ["enhancement"], date(2026, 10, 18))
    assert "## 2026-10-18" in result and "### Features" in result and "(#42) by @ada" in result
