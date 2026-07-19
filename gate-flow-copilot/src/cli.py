"""Command-line entry point for Gate-Flow Co-Pilot.

Displays live gate statuses and an AI-generated crowd-redirection
recommendation.  This file is intentionally thin — all business logic
lives in the domain modules.
"""

from __future__ import annotations

import argparse

from src.config import DEFAULT_MINUTES_TO_KICKOFF, STADIUM_NAME
from src.crowd_simulator import GateStatus, simulate_gate_densities
from src.recommender import get_recommendation
from src.translator import format_multilingual_output, translate_recommendation

# ---------------------------------------------------------------------------
# Display helpers (presentation only — no business logic)
# ---------------------------------------------------------------------------


def _render_gate_table(statuses: list[GateStatus]) -> str:
    """Format gate statuses as a compact ASCII table.

    Args:
        statuses: Current density snapshot for every gate.

    Returns:
        A formatted multi-line string.
    """
    header: str = f"{'Gate':<12} {'Zone':<28} {'Density':>8}  {'Status':<10}"
    separator: str = "─" * len(header)
    rows: list[str] = [separator, header, separator]

    for status in statuses:
        bar_len: int = int(status.density_pct / 5)
        density_bar: str = "█" * bar_len + "░" * (20 - bar_len)
        rows.append(
            f"{status.gate.name:<12} {status.gate.zone:<28} "
            f"{status.density_pct:>6.1f} %  {density_bar} {status.label}"
        )

    rows.append(separator)
    return "\n".join(rows)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace with ``minutes`` and ``seed`` attributes.
    """
    parser = argparse.ArgumentParser(
        description="Gate-Flow Co-Pilot — AI crowd-management assistant",
    )
    parser.add_argument(
        "-m",
        "--minutes",
        type=int,
        default=DEFAULT_MINUTES_TO_KICKOFF,
        help="Minutes until kickoff (default: 30)",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducible simulation",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run the Gate-Flow Co-Pilot CLI.

    Args:
        argv: Optional argument list for testing.
    """
    args: argparse.Namespace = _parse_args(argv)

    print(f"\n🏟️  {STADIUM_NAME}")
    print(f"⏱️  {args.minutes} minutes to kickoff\n")

    # 1. Simulate gate densities
    statuses: list[GateStatus] = simulate_gate_densities(
        minutes_to_kickoff=args.minutes,
        seed=args.seed,
    )
    print(_render_gate_table(statuses))

    # 2. Get AI recommendation
    print("\n🤖 AI Recommendation:\n")
    recommendation: str = get_recommendation(statuses)

    # 3. Translate and display
    translations: dict[str, str] = translate_recommendation(recommendation)
    print(format_multilingual_output(translations))
    print()


if __name__ == "__main__":
    main()
