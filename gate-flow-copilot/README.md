# Gate-Flow Co-Pilot

An AI crowd-management assistant for **MetLife Stadium, East Rutherford, New Jersey** — a FIFA World Cup 2026 venue. Built for the PromptWars Challenge 4.

## Problem statement

Large single-day events funnel tens of thousands of fans through a handful of gates in a short window. Congestion at one gate while a nearby gate sits idle is a safety and experience problem, and it's made worse when volunteers, fans, and staff don't have simple, real-time, multilingual guidance. Gate-Flow Co-Pilot targets that root problem directly:

- **Volunteers** get a live, plain-language, multilingual recommendation for which gates to redirect fans away from and toward, generated from real-time density data rather than guesswork.
- **Fans** get a rule-based "which gate should I use for my seat" lookup, GenAI-grounded wayfinding to points of interest, an accessibility Q&A grounded in fixed venue facts, and a transport recommendation for arriving or leaving.
- **Staff** get a sustainability view surfacing which waste/recycling bins need attention before they overflow.

Every GenAI-backed feature (recommendations, navigation, translation, accessibility Q&A) has a deterministic rule-based fallback, so the tool keeps working if the model API is slow, rate-limited, or down — appropriate for a live-event safety tool.

## Architecture

```
Fan / Volunteer (browser)
        │
        ▼
  React frontend (frontend/)
        │  fetch /api/*
        ▼
  Flask API (src/web.py)
        │
        ├── src/crowd_simulator.py    (gate density simulation)
        ├── src/recommender.py         (volunteer recommendation: GenAI + fallback)
        ├── src/navigation_assistant.py (fan wayfinding: GenAI + fallback)
        ├── src/accessibility_assistant.py (Q&A: GenAI + fallback)
        ├── src/translator.py           (multilingual output: GenAI + fallback)
        ├── src/fan_assistant.py         (rule-based gate lookup)
        ├── src/transport_assistant.py (rule-based transport advice)
        ├── src/sustainability.py        (bin levels + tips)
        └── src/genai_client.py           (single shared Gemini API call)
```

```
src/
  config.py                  # Stadium/gate/section constants, API key loading, shared GenAI model name
  crowd_simulator.py          # Deterministic-when-seeded gate density simulation
  genai_client.py               # Single shared low-level Gemini API call
  recommender.py               # Volunteer-facing GenAI recommendation + rule-based fallback
  translator.py                 # Concurrent multi-language translation + fallback
  navigation_assistant.py    # Fan wayfinding, congestion-aware, GenAI + fallback
  accessibility_assistant.py  # Fact-grounded accessibility Q&A, GenAI + fallback
  fan_assistant.py             # Rule-based nearest-gate lookup (no GenAI needed)
  transport_assistant.py     # Rule-based arrival/departure transport advice
  sustainability.py             # Bin fill-level simulation + tip generation
  web.py                          # Flask JSON API wiring the above together
  cli.py                           # Terminal entry point (gate table + AI recommendation)
frontend/                     # React + Vite single-page app, one tab per assistant
tests/                          # pytest suite, one file per src module
```

Each GenAI-backed module owns its own `_call_genai` wrapper (rather than one shared helper) so a failure in one assistant is isolated from the others and each can be mocked independently in tests — a deliberate tradeoff documented in `pyproject.toml`. All modules share a single `GENAI_MODEL` constant from `config.py` so upgrading models is a one-line change.

## Assumptions

- **Single venue, single event**: the simulation models one stadium (MetLife) hosting one match at a time — not a multi-venue or multi-day festival scenario.
- **Simulated, not live, gate data**: `crowd_simulator.py` generates realistic-looking density numbers from time-to-kickoff and gate capacity rather than reading real turnstile or camera sensor feeds, since no live venue data source was available for this challenge.
- **English as the source language**: all GenAI-generated text (recommendations, navigation, accessibility answers) is produced in English first, then translated on request — there's no assumption that any one language is the fan's native language beyond that starting point.
- **Single-instance deployment by default**: rate limiting and caching use in-memory storage, which is correct for a single-process demo deployment; a multi-instance production deployment would need `REDIS_URL` set (already supported) for both to work correctly across instances.
- **Fallback quality is "good enough," not identical**: when the GenAI API is unavailable, each assistant falls back to deterministic, rule-based text. That fallback text is clear and correct but intentionally simpler than what the model would produce — the goal is that the tool never goes silent, not that the fallback is indistinguishable from the AI output.

## Running it

Backend:

```bash
pip install -r requirements.txt
cp .env.example .env   # add your GENAI_API_KEY
python -m src.cli               # terminal demo
python -m src.web               # JSON API on http://127.0.0.1:5000
```

Frontend:

```bash
cd frontend
npm install
npm run dev              # http://localhost:5173
```

Tests:

```bash
pytest --cov=src --cov-report=term-missing
```

CI (`.github/workflows/ci.yml`) runs the backend test suite with a 90% coverage floor and builds the frontend on every push and pull request.
