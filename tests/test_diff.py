from prpilot.diff import changed_right_lines, validate_findings
from prpilot.models import Finding


PATCH = """@@ -10,3 +10,4 @@ def x():
 context
-old()
+new()
+another()
 tail
"""


def finding(line: int) -> Finding:
    return Finding("high", "src/app.py", line, "Broken behavior", "Use a safe value", "bug", 0.9)


def test_changed_right_lines_excludes_context_and_removed_lines():
    assert changed_right_lines(PATCH) == {11, 12}


def test_validation_only_accepts_actual_added_lines():
    accepted, rejected = validate_findings([finding(11), finding(10), finding(99)], [{"filename": "src/app.py", "patch": PATCH}])
    assert accepted == [finding(11)]
    assert len(rejected) == 2
