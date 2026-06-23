# Final Task Breakdown – CodeSense Hardening Sprint

## Overview
The list below is ordered by **dependency** (what must exist before the next item can be implemented) and grouped by the **priority** you specified.  Each item includes a rough effort estimate (developer‑days) to help plan the sprint.  All tasks are low‑risk, incremental changes that keep the existing architecture intact.

---

## 📌 Priority 1 – Core Functionality (≈ 12 dev‑days)

### 1️⃣ Repository Dashboard & Management (2 days)
- Create `RepositoryCard` component (vanilla React) showing name, branch, file count, chunk count, embedding count, size, last indexed, indexing status.
- Add UI for **Re‑index** and **Delete** buttons on each card.
- Implement API endpoints:
  - `GET /repositories` (list with stats)
  - `PUT /repositories/{id}/reindex`
  - `DELETE /repositories/{id}`
- Wire dashboard route `/repositories` in `App.jsx`.

### 2️⃣ Repository Metadata & Statistics (2 days)
- Extend ORM `Repository` model with columns `file_count`, `chunk_count`, `embedding_count`, `last_indexed_at`, `indexing_duration`, `indexing_status` (already added via migration).
- Add `GET /repositories/{id}` returning full metadata.
- Update existing indexing flow to populate these fields after a successful index.

### 3️⃣ Persistent Conversations (2 days)
- Add `Conversation` and `Message` tables (already present) and FastAPI CRUD endpoints:
  - `GET /repositories/{repo_id}/conversations`
  - `POST /repositories/{repo_id}/conversations`
  - `PUT /conversations/{id}` (rename/pin)
  - `DELETE /conversations/{id}`
- Frontend components:
  - Conversation list sidebar
  - Buttons for rename, delete, pin
  - Persist chat history via DB.

### 4️⃣ Markdown Rendering & Syntax Highlighting (1 day)
- Install `react-markdown` and `highlight.js` (dev dependencies).
- Wrap chat response component to render markdown safely and apply syntax highlighting for code fences.

### 5️⃣ Source References & Clickable Links (1 day)
- Include `source_file` metadata in each `Message` (already in vector chunk metadata).
- UI: clickable file path that opens a modal showing the snippet (highlighted).

### 6️⃣ Saved Reports & PDF Export (2 days)
- ORM `Report` model already created.
- Endpoint `POST /repositories/{id}/reports` → generates markdown + PDF via **WeasyPrint**.
- Store PDF bytes on disk (or as BLOB) and store path in DB.
- Frontend: "Reports" page showing list, view, download (MD/PDF) buttons.

### 7️⃣ Analytics Dashboard (1 day)
- New tables `analytics_events`, `usage_metrics`, `repository_stats` (see migration below).
- Simple endpoint `GET /analytics/summary` returning totals.
- Frontend dashboard widget on the main page displaying totals.

### 8️⃣ Centralized Error Handling (1 day)
- Add FastAPI middleware that catches all exceptions and returns a unified JSON shape:
  ```json
  {"success": false, "error": {"code": "<CODE>", "message": "<msg>"}}
  ```
- Strip stack traces from responses, log them internally with Loguru.

---

## 📌 Priority 2 – Polish & Docs (≈ 6 dev‑days)

### 9️⃣ Responsive & Dark‑Mode Consistency (1 day)
- Verify Tailwind‑like CSS variables for colors; add media query for `prefers-color-scheme`.
- Ensure all components use the same spacing/typography tokens.

### 10️⃣ Loading & Empty States (1 day)
- Skeleton loaders for dashboard cards and conversation list.
- Empty‑state components for no repositories, no conversations, and failed indexing.

### 11️⃣ Toast Notifications (1 day)
- Tiny reusable toast component (vanilla) for success/error messages (e.g., re‑index started, delete confirmed).

### 12️⃣ Documentation (2 days)
- Update `README.md` with setup, architecture diagram (Mermaid), and usage steps.
- Add `docs/api.md` generated from FastAPI OpenAPI schema.
- Add a `CONTRIBUTING.md` with linting (ruff), type‑checking (mypy), and pre‑commit hooks.

---

## 📦 Migration Strategy (≈ 2 dev‑days total)
- Use **Alembic‑style** simple SQL scripts stored in `backend/migrations/` (no external dependency required).
- First migration creates all tables defined in `models_orm.py`.
- Subsequent migration adds new columns for repository stats and analytics.
- The app will call `Base.metadata.create_all()` **only** when `ENV == "development"` (fallback).
- Document commands:
  ```bash
  python -m backend.migrations upgrade
  python -m backend.migrations downgrade -1
  ```
- Include rollback SQL statements in each script comment.

---

## 📊 Security & Performance Improvements (cross‑cutting)
- **Auth hardening**: validate `session_id` cookie, add expiration check (e.g., 24 h), ensure `secure` and `httponly` flags set when served over HTTPS.
- **Ownership checks** on every protected endpoint (`repo_id` belongs to `current_user`).
- **Rate limiting** middleware (fastapi‑limiter) – 60 requests per minute per IP.
- **Logging**: structured Loguru config with request ID (`X-Request-ID` header), filter out `session_id` and any API keys.
- **Environment validation** at startup – abort with clear message if `DATABASE_URL`, `GROQ_API_KEY`, `GITHUB_TOKEN`, or vector DB vars missing.

---

## 📋 Deliverables
1. Updated **task.md** (this file) – ordered list with estimates.
2. Migration scripts in `backend/migrations/`.
3. New ORM models (`models_orm.py`) and updated `database.py`.
4. Auth helper (`auth.py`) with hardened validation.
5. FastAPI middleware for errors, rate‑limit, logging.
6. Frontend components for dashboard, conversations, reports, analytics.
7. Documentation files (`README.md`, `docs/api.md`, `CONTRIBUTING.md`).
8. Updated CI‑friendly scripts (`run_dev.sh`/`run_prod.sh`).

The total estimated effort is **~ 18 developer‑days** (~ 3 weeks for a single developer) which fits the “single implementation pass” constraint while keeping each change low‑risk.

---

*All tasks respect the existing architecture, use vanilla React/CSS, keep embeddings in the current vector store, and store everything else in PostgreSQL.*
