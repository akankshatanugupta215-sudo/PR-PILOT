import pytest

from prpilot.gemini import parse_analysis


def test_parse_analysis_discards_invalid_finding_but_keeps_valid_one():
    response = '''{"summary":"Review complete","findings":[
      {"severity":"high","category":"bug","filename":"src/a.py","line":5,"explanation":"Null dereference","suggested_fix":"Check for None","confidence":0.9,"heuristic":false},
      {"severity":"urgent","category":"bug","filename":"src/a.py","line":1,"explanation":"bad","suggested_fix":"fix","confidence":1,"heuristic":false}
    ]}'''
    analysis = parse_analysis(response)
    assert analysis.summary == "Review complete"
    assert len(analysis.findings) == 1


def test_parse_analysis_rejects_non_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_analysis("not JSON")
