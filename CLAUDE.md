# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ImageLab is a web application for visual, block-based image processing. Users compose pipelines by dragging and connecting blocks in a Google Blockly editor, then the backend executes those pipelines server-side with OpenCV (Python). The repo also contains a legacy Electron desktop app (under `electron-app-legacy/`) and a Jekyll documentation site (`docs/`).

## Repository Structure

- **`imagelab-frontend/`** — React 19 + TypeScript + Vite SPA with Blockly editor
- **`imagelab-backend/`** — Python FastAPI server with `opencv-python-headless`
- **`docs/`** — Jekyll documentation site
- **`electron-app-legacy/`** — Legacy Electron desktop version, kept for reference

## Common Commands

### Backend (from `imagelab-backend/`)

```bash
cp .env.example .env
uv sync                                              # Install dependencies
uv run uvicorn app.main:app --reload --port 4100    # Run dev server
uv run pytest -v                                     # Run all tests
uv run ruff check .                                  # Lint
uv run ruff check --fix .                            # Auto-fix lint issues
uv run ruff format .                                 # Format
uv run ruff format --check .                         # Check formatting
uv run alembic upgrade head                          # Run DB migrations
uv run alembic revision --autogenerate -m "desc"     # Generate new migration
```

### Frontend (from `imagelab-frontend/`)

```bash
cp .env.example .env
npm install                    # Install dependencies
npm run dev                    # Dev server (port 3100)
npm run build                  # Production build (tsc -b && vite build)
npm run test                   # Run Vitest tests
npm run test:watch             # Run Vitest in watch mode
npm run lint                   # ESLint check
npm run format                 # Prettier
npm run preview                # Preview production build
```

### Docker (from repo root)

```bash
docker-compose up              # Run full stack (db + backend + frontend)
```

## Ports

| Service    | Port |
|------------|------|
| Frontend   | 3100 |
| Backend    | 4100 |
| PostgreSQL | 5432 |

## Architecture

### Backend

**Framework:** FastAPI (titled "ImageLab API"), exported as `app` in `imagelab-backend/app/main.py`.

**Layered structure:**
- `app/routers/` — API route definitions, mounted under `/api`
- `app/services/` — Pipeline executor and business logic
- `app/operators/` — Operator registry and per-category operator implementations
- `app/models/` — Pydantic/SQLModel request and response schemas
- `app/utils/` — Image decode/encode helpers
- `app/config.py` — pydantic-settings configuration
- `app/exceptions.py` — Exception handler registration

**API routes** (all under `/api`):

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/health | Health check |
| POST | /api/pipeline/execute | Execute an image processing pipeline |

**Operator registry pattern:** Operators live in `app/operators/`, grouped into 11 categories. Each operator class registers itself by string type with `app/operators/registry.py`. `get_operator(type)` returns the class, the executor instantiates it with the step's params, then calls `compute(image)`.

Operator categories: `augmentation`, `basic`, `blurring`, `conversions`, `drawing`, `filtering`, `geometric`, `segmentation`, `sobel_derivatives`, `thresholding`, `transformation`.

**Pipeline executor** (`app/services/pipeline_executor.py`): iterates through `PipelineRequest.pipeline`, skips operators in `NOOP_TYPES`, calls the operator's `compute(image)`, records per-step timings, and re-encodes the result to base64. Always returns a `PipelineResponse` with `timings` populated, even on partial failure (so the frontend can show which step failed and how long earlier steps took).

**Request/response models** (`app/models/pipeline.py`): `PipelineStep` (type + params), `PipelineRequest` (base64 image + image_format + steps), `PipelineResponse` (success, image, error, step, timings), `StepTiming` (step, operator_type, duration_ms), `PipelineTimings` (total_ms, steps).

**Database:** PostgreSQL via SQLModel/SQLAlchemy. Alembic migrations in `alembic/versions/`. Migrations auto-run on app startup via the lifespan handler. The current pipeline API does not persist anything, so the DB layer is scaffolded but minimally used.

**Image transport:** All images are base64-encoded strings on the wire (both request and response). Decode/encode helpers live in `app/utils/image.py`.

**Config:** `app/config.py` (pydantic-settings) reads env vars. Required: `CORS_ORIGINS`, `DATABASE_URL`. See `.env.example`.

### Frontend

**Stack:** React 19 + TypeScript + Vite, Google Blockly 12 (with `field-angle`, `field-colour`, `field-slider`, `workspace-search` plugins), Zustand for state, Tailwind CSS 4, Vitest for tests, Lucide React for icons.

**No React Router.** It is a single-page app whose flow is driven by component state (landing screen, then main workspace).

**Source layout** (`src/`):
- `App.tsx`, `main.tsx`, `index.css` — Root
- `blockly-setup.ts` — Blockly workspace configuration and registration
- `api/pipeline.ts` — Axios-less HTTP client for `POST /api/pipeline/execute`
- `blocks/` — Block definitions (one file per operator category), `categories.ts`, `theme.ts`, `extensions/`
- `components/` — UI: Navbar, Layout, Toolbar, Sidebar, Preview, modals (camera capture, keyboard shortcuts, share pipeline), LandingScreen, ErrorBoundary, InfoPane
- `hooks/` — `useBlocklyWorkspace`, `usePipeline`, `useBlockPreviews`, `useDarkMode`, `useKeyboardShortcuts`, `useSidebarDrag`, `imagePersistence`, `workspacePersistence`
- `store/pipelineStore.ts` — Single Zustand store for pipeline state, execution state, and results
- `types/pipeline.ts` — TypeScript types mirroring the backend models
- `data/operatorDocs.ts` — Inline operator documentation
- `utils/` — `blockLimits`, `canvas`, `imageData`

**Workspace persistence:** The Blockly workspace and the input image are persisted to `localStorage` via `hooks/workspacePersistence.ts` and `hooks/imagePersistence.ts`.

**Dark mode:** Toggled via `useDarkMode`, applied through Tailwind classes plus a Blockly theme switch in `blocks/theme.ts`.

**API base URL:** Configured via `VITE_API_URL` env var (default: `http://localhost:4100`).

## Code Style

### Backend (Python)
- **Linter/formatter:** Ruff (line-length 120, target Python 3.12)
- **Rules:** E, F, I (isort), UP, B, SIM
- **Quotes:** Double quotes
- **Testing:** pytest with `testpaths = ["tests"]`, `pythonpath = ["."]`

### Frontend (TypeScript)
- **Linter:** ESLint 9 with `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
- **Formatter:** Prettier 3
- **TypeScript:** Three configs (`tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`)
- **Testing:** Vitest + @testing-library/react

## Gotchas

- The pipeline endpoint (`POST /api/pipeline/execute`) uses sync `def`, not `async def`. This is intentional. OpenCV operations are CPU-bound and FastAPI dispatches `def` handlers to a thread pool via `anyio.to_thread.run_sync`, which keeps the event loop responsive. Do not convert to `async def` unless `execute_pipeline()` itself becomes fully async. The reasoning is documented inline in `app/routers/pipeline.py`.
- Certain operator types are intentionally skipped during execution. The `NOOP_TYPES` set in `pipeline_executor.py` includes `basic_readimage`, `basic_writeimage`, `border_for_all`, `border_each_side`. These are placeholders in the block UI that do not correspond to runtime operations.
- The operator registry is initialized at module import time and is never mutated afterward, which is what makes the executor safe to call concurrently from FastAPI's thread pool.
- Alembic migrations run automatically on startup in the FastAPI lifespan. On failure, the app logs a warning and starts without database features rather than crashing, so a missing PostgreSQL connection will not block the pipeline endpoint.
- All images on the wire are base64 strings, so very large images mean correspondingly large payloads. Encode/decode is handled in `app/utils/image.py` (backend) and `src/utils/imageData.ts` (frontend).
- The frontend default `VITE_API_URL` is `http://localhost:4100`. If the backend runs elsewhere (Docker network, remote host), update `.env` accordingly.
- `npm run build` runs `tsc -b` before `vite build`, so a TypeScript error will fail the build even if Vite alone would succeed.
