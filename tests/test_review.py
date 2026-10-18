from prpilot.models import Finding
from prpilot.review import heuristic_warnings, labels_for


def test_label_mapping_includes_finding_and_changed_test_doc_labels():
    finding = Finding("high", "src/a.py", 1, "unsafe", "validate", "security", 0.8)
    assert labels_for([finding], {"tests": ["tests/test_a.py"], "documentation": ["README.md"]}) == ["documentation", "security", "tests"]


def test_missing_tests_and_docs_are_heuristics_not_failures():
    tests, docs = heuristic_warnings([{"filename": "src/a.py"}], {})
    assert tests and tests.startswith("Heuristic warning")
    assert docs and "not a verified failure" in docs
