"""Unit tests for the CLI entry point.

GenAI calls (via recommender/translator) are mocked so the suite runs
fully offline.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.cli import _parse_args, _render_gate_table, main
from src.crowd_simulator import simulate_gate_densities


class TestParseArgs:
    """Tests for command-line argument parsing."""

    def test_defaults(self) -> None:
        args = _parse_args([])
        assert args.minutes == 30
        assert args.seed is None

    def test_custom_minutes_and_seed(self) -> None:
        args = _parse_args(["--minutes", "15", "--seed", "42"])
        assert args.minutes == 15
        assert args.seed == 42

    def test_short_flags(self) -> None:
        args = _parse_args(["-m", "5", "-s", "1"])
        assert args.minutes == 5
        assert args.seed == 1

    def test_invalid_minutes_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_args(["--minutes", "not-a-number"])


class TestRenderGateTable:
    """Tests for the ASCII gate-status table renderer."""

    def test_includes_every_gate_name(self) -> None:
        statuses = simulate_gate_densities(minutes_to_kickoff=30, seed=1)
        table = _render_gate_table(statuses)
        for status in statuses:
            assert status.gate.name in table

    def test_returns_nonempty_string(self) -> None:
        statuses = simulate_gate_densities(minutes_to_kickoff=30, seed=1)
        assert len(_render_gate_table(statuses)) > 0


class TestMain:
    """End-to-end tests for the main() entry point (API calls mocked)."""

    @patch("src.cli.translate_recommendation")
    @patch("src.cli.get_recommendation")
    def test_runs_without_error(self, mock_rec, mock_translate, capsys) -> None:
        mock_rec.return_value = "Head to Gate C, it has the lowest density."
        mock_translate.return_value = {"English": mock_rec.return_value}

        main(["--minutes", "20", "--seed", "7"])

        captured = capsys.readouterr()
        assert "AI Recommendation" in captured.out
        assert "Gate C" in captured.out

    @patch("src.cli.translate_recommendation")
    @patch("src.cli.get_recommendation")
    def test_default_args_run_without_error(self, mock_rec, mock_translate, capsys) -> None:
        mock_rec.return_value = "All gates are flowing smoothly."
        mock_translate.return_value = {"English": mock_rec.return_value}

        main([])

        captured = capsys.readouterr()
        assert "minutes to kickoff" in captured.out
