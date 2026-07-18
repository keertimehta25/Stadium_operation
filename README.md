# Gate-Flow Co-Pilot

A GenAI-enabled operations assistant for FIFA World Cup 2026 venues — built for MetLife Stadium as a reference deployment. It supports fans, volunteers, and venue staff with real-time, AI-generated guidance across crowd management, navigation, accessibility, transportation, sustainability, and multilingual assistance.

## Why this exists

The tournament experience breaks down at a few predictable friction points: fans don't know which gate is least crowded, they can't find a restroom or medical station quickly, accessibility questions go unanswered until they reach a help desk, and non-English speakers get none of the above. Gate-Flow Co-Pilot addresses each of these with a GenAI layer on top of live (simulated) operational data, with deterministic rule-based fallbacks so the experience never goes fully dark if the API is unavailable.

## Features

| Module | What it does |
|---|---|
| **Crowd Management** | Simulates live gate density and generates a plain-language redirection recommendation for volunteers/staff |
| **Fan Gate Lookup** | Given a seating section, recommends the least congested entry gate |
| **Navigation** | GenAI-generated turn-by-turn style directions between gates, sections, and points of interest (restrooms, medical, guest services, elevators) — factors in **live gate congestion** near the destination, so guidance can flag a busy entrance and suggest an alternate, making this real-time decision support rather than static wayfinding |
| **Accessibility Assistant** | Free-text Q&A grounded in venue accessibility facts (mobility, sensory, hearing, service animals, companion seating, parking) |
| **Transportation** | Recommends arrival/departure transport modes based on time to kickoff |
| **Sustainability** | Tracks simulated waste-bin fill levels and surfaces sustainability tips |
| **Multilingual Assistance** | Translates the crowd-management recommendation into multiple languages in parallel |

## Architecture

```
gate-flow-copilot/
├── src/                            # Flask API + domain logic (Python)
│   ├── web.py                      # HTTP routes — thin, delegates to domain modules
│   ├── cli.py                      # Standalone terminal demo
│   ├── config.py                   # Stadium/section/gate configuration
│   ├── crowd_simulator.py          # Gate density simulation
│   ├── recommender.py              # GenAI crowd-redirection recommendation + fallback
│   ├── navigation_assistant.py     # GenAI wayfinding + live-density-aware routing
│   ├── accessibility_assistant.py  # Grounded GenAI accessibility Q&A
│   ├── transport_assistant.py      # Transport mode recommendation
│   ├── sustainibility.py           # Bin-level simulation + tips
│   └── translator.py               # Multilingual translation (cached, parallelized)
├── frontend/                       # React + Vite dashboard
│   └── src/components/             # One component per view/tab
├── tests/                          # pytest suite, GenAI calls mocked, 97% coverage
├── .github/workflows/ci.yml        # CI: tests + coverage gate + frontend build
└── requirements.txt
```

Every GenAI-backed module follows the same pattern: build a prompt → call the API → on any failure, fall back to a deterministic rule-based response. Nothing user-facing ever hard-fails because of an API outage or missing key.

## Setup

### Backend

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Gemini API key:

```
GEMINI_API_KEY=your-key-here
```

Run the API server:

```bash
python -m src.web
```

The API listens on `http://127.0.0.1:5000`. Sanity-check it's fully wired:

```bash
python -c "import src.web; print(src.web.app.url_map)"
```

Or try the standalone CLI demo (no frontend needed):

```bash
python -m src.cli
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`, with API calls proxied to the Flask backend (see `frontend/vite.config.js`). For a production build, set `VITE_API_BASE_URL` to your deployed backend's URL before running `npm run build`.

## Running tests

```bash
pytest --cov=src --cov-report=term-missing
```

All GenAI API calls are mocked in tests — the suite runs fully offline and never makes billed API requests. Current coverage: **97%** across 123 tests. Every `_call_genai`-style function is tested both through its public wrapper (mocked at that boundary) and directly at the `genai.Client` boundary (covering the empty-response error path), not just the happy path.

## Continuous Integration

Every push and PR to `main` runs via GitHub Actions (`.github/workflows/ci.yml`):
- **Backend**: installs dependencies, runs the full pytest suite, and fails the build if coverage drops below 90%
- **Frontend**: installs dependencies and runs a production Vite build, catching build-breaking errors before they reach deployment

## Security notes

- CORS is restricted to explicit origins in `src/web.py` — local dev origins are always allowed, and production origins (e.g. your Vercel deployment URL) are added via the `ALLOWED_ORIGINS` env var (comma-separated) without touching code.
- Baseline security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`) are attached to every response.
- GenAI-backed endpoints (`/api/status`, `/api/navigate`, `/api/accessibility`) are rate-limited via `flask-limiter` to prevent abuse of billed API calls. Uses in-memory storage by default (fine for a single-instance demo); set `REDIS_URL` to switch to persistent, multi-instance-safe storage in production without any code changes.
- `.env` is git-ignored — never commit API keys.
- Free-text input to the accessibility assistant is length-capped and the prompt explicitly instructs the model to ignore embedded instructions, to reduce prompt-injection risk.

## Accessibility

The frontend implements WAI-ARIA tab semantics (`role`/`aria-selected`, arrow-key navigation), a skip-to-content link, visible focus states on all interactive elements, `aria-live` regions for dynamic content, and a high-contrast theme toggle.

Color contrast has been verified against WCAG 2.1 AA (4.5:1 minimum for normal text) using the actual CSS variable values, not eyeballed:

| Pair | Ratio | AA (normal text) |
|---|---|---|
| Primary text on background | 18.30:1 | Pass |
| Muted text on background | 7.93:1 | Pass |
| Low-density indicator on background | 7.94:1 | Pass |
| Moderate-density indicator on background | 9.37:1 | Pass |
| High-density indicator on background | 5.35:1 | Pass |
| Focus/accent color on background | 4.75:1 | Pass |

## License

Built for the PromptWars Challenge 4 submission.
