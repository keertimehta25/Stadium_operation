"""Flask API server for Gate-Flow Co-Pilot.

Serves JSON only — the browser UI now lives in the React app under
frontend/. This file wires HTTP requests to the domain modules; no
business logic lives here.
"""

from __future__ import annotations

import os

from flask import Flask, Response, jsonify, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src.accessibility_assistant import get_accessibility_answer
from src.config import SECTIONS, STADIUM_NAME
from src.crowd_simulator import GateStatus, simulate_gate_densities
from src.fan_assistant import recommend_gate_for_section
from src.navigation_assistant import find_pois, get_directions
from src.recommender import get_recommendation
from src.sustainability import simulate_bin_levels, sustainability_tip
from src.translator import translate_recommendation
from src.transport_assistant import recommend_transport

app = Flask(__name__)

# CORS: restrict to known frontend origins instead of allowing "*".
# Local dev origins are always allowed; add production origins (e.g. your
# Vercel deployment URL) via the ALLOWED_ORIGINS env var, comma-separated.
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
CORS(app, resources={r"/api/*": {"origins": _default_origins + _extra_origins}})

# Rate limiting protects the GenAI-backed endpoints (billed API calls)
# from abuse or a runaway polling loop on the frontend. Uses in-memory
# storage by default (fine for a single-instance demo deployment); set
# REDIS_URL to use persistent, multi-instance-safe storage in production.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["60 per minute"],
    storage_uri=os.environ.get("REDIS_URL", "memory://"),
)


@app.after_request
def _set_security_headers(response: Response) -> Response:
    """Attach baseline security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


_MIN_MINUTES = 0
_MAX_MINUTES = 240
_MAX_LOCATION_LENGTH = 80


def _parse_minutes(raw: int) -> int:
    """Clamp a requested minutes-to-kickoff value into a safe range."""
    return max(_MIN_MINUTES, min(raw, _MAX_MINUTES))


def _clean_text(raw: str, max_length: int) -> str:
    """Trim and length-cap free-text input before it reaches any prompt."""
    return raw.strip()[:max_length]


def build_snapshot(minutes: int, seed: int | None) -> dict:
    """Assemble a JSON-serialisable gate-status + recommendation snapshot."""
    statuses: list[GateStatus] = simulate_gate_densities(minutes_to_kickoff=minutes, seed=seed)
    recommendation: str = get_recommendation(statuses)
    translations: dict[str, str] = translate_recommendation(recommendation)
    return {
        "stadium": STADIUM_NAME,
        "minutes_to_kickoff": minutes,
        "gates": [
            {
                "name": s.gate.name,
                "zone": s.gate.zone,
                "density": s.density_pct,
                "status": s.label,
            }
            for s in statuses
        ],
        "translations": translations,
    }


@app.get("/")
def index() -> str:
    """Render a basic dashboard shell with stadium name."""
    return f"<html><body><h1>{STADIUM_NAME}</h1></body></html>"


@app.get("/api/status")
@limiter.limit("20 per minute")
def api_status() -> ResponseReturnValue:
    """Return a fresh gate-status + recommendation snapshot as JSON."""
    minutes = _parse_minutes(request.args.get("minutes", default=30, type=int))
    seed = request.args.get("seed", default=None, type=int)
    return jsonify(build_snapshot(minutes, seed))


@app.get("/api/sections")
def api_sections() -> ResponseReturnValue:
    """Return the list of configured seating sections."""
    return jsonify([s.section for s in SECTIONS])


@app.get("/api/fan-gate")
def api_fan_gate() -> ResponseReturnValue:
    """Recommend the best entry gate for a fan's seating section."""
    section = request.args.get("section", default="", type=str)
    minutes = _parse_minutes(request.args.get("minutes", default=30, type=int))
    seed = request.args.get("seed", default=None, type=int)

    statuses = simulate_gate_densities(minutes_to_kickoff=minutes, seed=seed)
    result = recommend_gate_for_section(section, statuses)

    status_code = 400 if "error" in result else 200
    return jsonify(result), status_code


@app.get("/api/transport")
def api_transport() -> ResponseReturnValue:
    """Recommend a transportation mode for arriving at or leaving the venue."""
    minutes = _parse_minutes(request.args.get("minutes", default=30, type=int))
    post_match = request.args.get("post_match", default="false", type=str).lower() == "true"
    return jsonify(recommend_transport(minutes, post_match))


@app.get("/api/sustainability")
def api_sustainability() -> ResponseReturnValue:
    """Return current bin fill levels and a sustainability tip."""
    seed = request.args.get("seed", default=None, type=int)
    statuses = simulate_bin_levels(seed)
    return jsonify(
        {
            "bins": [{"zone": s.zone, "type": s.bin_type, "fill": s.fill_pct} for s in statuses],
            "tip": sustainability_tip(statuses),
        }
    )


@app.get("/api/pois")
def api_pois() -> ResponseReturnValue:
    """Return points of interest (restrooms, medical, elevators, etc.)."""
    category = request.args.get("category", default=None, type=str)
    pois = find_pois(category)
    return jsonify(
        [
            {
                "name": p.name,
                "category": p.category,
                "nearest_gate": p.nearest_gate,
                "zone": p.zone,
                "notes": p.notes,
            }
            for p in pois
        ]
    )


@app.get("/api/navigate")
@limiter.limit("20 per minute")
def api_navigate() -> ResponseReturnValue:
    """Return GenAI-generated wayfinding directions between two locations.

    Directions factor in live gate congestion near the destination, so
    guidance can flag a busy entrance and suggest expecting a short wait
    or using a nearby alternate — this is what makes navigation real-time
    decision support rather than static wayfinding.
    """
    start = _clean_text(request.args.get("start", default="", type=str), _MAX_LOCATION_LENGTH)
    destination = _clean_text(
        request.args.get("destination", default="", type=str), _MAX_LOCATION_LENGTH
    )
    if not start or not destination:
        return jsonify({"error": "Both 'start' and 'destination' are required."}), 400

    minutes = _parse_minutes(request.args.get("minutes", default=30, type=int))
    gate_statuses = simulate_gate_densities(minutes_to_kickoff=minutes)
    return jsonify(get_directions(start, destination, gate_statuses))


@app.post("/api/accessibility")
@limiter.limit("15 per minute")
def api_accessibility() -> ResponseReturnValue:
    """Answer a free-text accessibility question, grounded in venue facts."""
    payload = request.get_json(silent=True) or {}
    question = _clean_text(str(payload.get("question", "")), 300)
    if not question:
        return jsonify({"error": "A 'question' field is required."}), 400
    return jsonify(get_accessibility_answer(question))


@app.errorhandler(404)
def not_found(_err: Exception) -> ResponseReturnValue:
    """Return a clean JSON 404 instead of Flask's default HTML page."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_err: Exception) -> ResponseReturnValue:
    """Return a clean JSON 500 without leaking internal stack traces."""
    return jsonify({"error": "Internal server error"}), 500


def main() -> None:
    """Run the Flask development server (API only, debug always off)."""
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
