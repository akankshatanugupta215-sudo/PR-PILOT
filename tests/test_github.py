from urllib.error import URLError

from prpilot.github import GitHubClient


def test_transient_network_error_is_retried(monkeypatch):
    calls = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'{"ok": true}'

    def fake_open(request, timeout):
        calls.append(request)
        if len(calls) == 1:
            raise URLError("temporary")
        return Response()

    monkeypatch.setattr("prpilot.github.urlopen", fake_open)
    client = GitHubClient("token", "owner/repo", retries=1, sleep=lambda _: None)
    assert client.request("GET", "/ok") == {"ok": True}
    assert len(calls) == 2
