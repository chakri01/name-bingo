## Quick orientation

This repo implements a simple Name-Bingo game with a FastAPI backend (Postgres + SQLAlchemy) and a Vite/React frontend.

- **Backend**: [backend/main.py](backend/main.py) (FastAPI app), [backend/models.py](backend/models.py), [backend/database.py](backend/database.py), [backend/tickets.py](backend/tickets.py)
- **Frontend**: [frontend/src/App.jsx](frontend/src/App.jsx), configured with Vite ([frontend/package.json](frontend/package.json))
- **Local dev (compose)**: [docker-compose.yml](docker-compose.yml) boots Postgres, backend, frontend
- **Cloud deploy**: [render.yaml](render.yaml) shows build/start commands and environment expectations

## High-level architecture / data flow

- The backend exposes REST endpoints (see [backend/main.py](backend/main.py)). Frontend talks to the backend via `VITE_API_URL`.
- The DB is Postgres. Tables are declared with SQLAlchemy models in [backend/models.py](backend/models.py). The app calls `Base.metadata.create_all()` on startup — there is no migration framework in this repo.
- Names are seeded from [backend/names.json](backend/names.json) at startup; tickets are pre-generated with `pre_generate_tickets()` (see [backend/tickets.py](backend/tickets.py)) and saved to the `tickets` table.
- Tickets store their `grid` as a JSONB column. Game state and some values use JSONB as well.
- Claim flow: users `POST /api/claim` → entries added to `claim_queue` → admin inspects `/api/admin/claims` and calls `/api/admin/verify-claim`. Locking is implemented with a DB advisory lock plus a `game_state` key (`claim_lock`) (see [backend/main.py](backend/main.py)).

## Important implementation details for code edits

- The backend expects `DATABASE_URL` environment variable. Local docker-compose sets `postgresql://postgres:postgres@db:5432/namebingo` (see [docker-compose.yml](docker-compose.yml)). `database.py` appends SSL settings when it detects `railway` in the URL.
- Tables are created at startup; don't assume migrations exist. If modifying models, either update the DB manually or ensure startup `create_all()` behavior is acceptable.
- `Ticket.grid` is JSONB; validators should operate on nested lists (ticket.grid is a 3x9 nested array with some nulls).
- `Name` rows track `is_picked`, `picked_at`, and `pick_order`. Picks are done with random choice in `/api/admin/pick-name` — keep pick ordering in mind when adding deterministic tests.
- Admin auth is a single password via env var `ADMIN_PASSWORD` (default `admin123`) checked in `/api/admin/login`. Admin requests expect an `Authorization` header in routes that require it (simple token behavior in this codebase).

## Developer workflows / commands

- Local (recommended quick start with Docker Compose):

```bash
docker-compose up --build
```

- Backend only (local venv):

```bash
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1    # Windows PowerShell
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Frontend dev:

```bash
cd frontend
npm install
npm run dev
```

- Render / production: see [render.yaml](render.yaml) for exact `buildCommand` and `startCommand` patterns used by the project.

## Patterns & conventions specific to this repo

- No migration tooling — schema changes are applied via SQLAlchemy `create_all()` on startup. Edits to models often require manual DB resets in dev.
- Use JSON/JSONB columns for structured fields (`Ticket.grid`, `GameState.value`). Treat these as canonical persisted data for game logic.
- Names and profiles live as source files in `backend/names.json` and `backend/profiles.json`. Profile data is served via `/api/profile/{name}` and may include `photo` and `bio`.
- Static assets for uploaded photos are placed under `backend/static/photos` and the app mounts `/static` (see [backend/main.py](backend/main.py)).

## Useful code examples (copyable)

- Register a player (frontend calls this):

```bash
curl -X POST http://localhost:8000/api/register -H 'Content-Type: application/json' -d '{"player_name":"Alice"}'
```

- Admin pick name (requires Authorization header in this codebase):

```bash
curl -X POST http://localhost:8000/api/admin/pick-name -H 'Authorization: admin_authenticated'
```

## Where to look when changing behavior

- Request/response definitions & routes: [backend/main.py](backend/main.py)
- DB models & schema: [backend/models.py](backend/models.py)
- Ticket generation logic: [backend/tickets.py](backend/tickets.py)
- DB connection and env handling: [backend/database.py](backend/database.py)
- Frontend routing and API composition: [frontend/src/App.jsx](frontend/src/App.jsx)

---
If anything here is unclear or you want the instructions adjusted (e.g., add more run examples, local test commands, or CI notes), tell me which parts to iterate on and I will update the file.
