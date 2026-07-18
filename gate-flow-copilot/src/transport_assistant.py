"""Transportation recommendation assistant.

Suggests the best way for a fan to get to or from the stadium, based
on time-to-kickoff (arrival) or whether the match has just ended
(departure). Pure rule-based logic — fast, deterministic, and easy to
test without any external API or GenAI call.
"""

from __future__ import annotations


def recommend_transport(minutes_to_kickoff: int, post_match: bool = False) -> dict:
    """Recommend a transportation mode for arriving at or leaving the stadium.

    Args:
        minutes_to_kickoff: Minutes remaining before kickoff. Ignored
            when post_match is True.
        post_match: If True, recommend a departure strategy instead of
            an arrival strategy.

    Returns:
        Dict with the recommended mode, an estimated wait, and a short
        explanatory note.
    """
    if post_match:
        return {
            "mode": "Rail / Transit",
            "wait_estimate": "20-30 min queue at the platform",
            "note": (
                "Departing crowds peak in the first 20 minutes after the "
                "final whistle. Waiting inside the concourse for 15 minutes "
                "before heading to the platform usually halves your wait."
            ),
        }

    if minutes_to_kickoff > 90:
        return {
            "mode": "Rideshare / Drive",
            "wait_estimate": "No queue",
            "note": "Parking lots are still open with plenty of space this early.",
        }
    if minutes_to_kickoff > 30:
        return {
            "mode": "Rail / Transit",
            "wait_estimate": "5-10 min",
            "note": "Trains are running frequently and platforms aren't yet crowded.",
        }
    return {
        "mode": "Shuttle + walk from drop-off",
        "wait_estimate": "10-15 min",
        "note": (
            "Roads near the stadium are congested this close to kickoff — "
            "shuttle plus a short walk beats driving or a rideshare pickup."
        ),
    }
