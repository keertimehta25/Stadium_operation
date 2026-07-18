"""Unit tests for src/config.py."""

from __future__ import annotations

import pytest

from src.config import GATES, SECTIONS, get_api_key


class TestGetApiKey:
    """Tests for GenAI API key retrieval."""

    def test_returns_key_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "test-key-123")
        assert get_api_key() == "test-key-123"

    def test_raises_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GENAI_API_KEY", raising=False)
        with pytest.raises(EnvironmentError):
            get_api_key()

    def test_raises_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "")
        with pytest.raises(EnvironmentError):
            get_api_key()


class TestConfigData:
    """Sanity checks on the static configuration data."""

    def test_gates_nonempty(self) -> None:
        assert len(GATES) > 0

    def test_sections_nonempty(self) -> None:
        assert len(SECTIONS) > 0

    def test_every_section_has_a_valid_primary_gate(self) -> None:
        gate_names = {g.name for g in GATES}
        for section in SECTIONS:
            assert section.primary_gate in gate_names
