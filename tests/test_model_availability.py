import pytest

from prpilot.gemini import verify_model_available


class Model:
    def __init__(self, name): self.name = name


class Models:
    def list(self): return [Model("models/gemini-3.8-flash")]


class Client:
    models = Models()


def test_configured_model_must_be_visible_to_api_key():
    verify_model_available(Client(), "gemini-3.8-flash")
    with pytest.raises(ValueError, match="unavailable"):
        verify_model_available(Client(), "not-a-model")
