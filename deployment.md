# TalentIQ — Local Setup and Environment Guide

**Repository:** https://github.com/Sankalp-gupta1/TalentIQ-AI-Resume-Screening  
**Deployment status:** No hosted deployment is configured or claimed. This guide covers local execution only.

## 1. Prerequisites

Recommended Docker path:
- Git: https://git-scm.com/downloads
- Docker Desktop / Docker Engine with Compose v2: https://www.docker.com/products/docker-desktop/
- Optional VS Code: https://code.visualstudio.com/

Verify:

```bash
git --version
docker --version
docker compose version
```

Direct development requires Python 3.12+, Node.js 22+ and npm. PostgreSQL/Redis are needed for a non-Docker production-like setup; the backend-only direct demo can use SQLite.

## 2. Get the source

```bash
git clone https://github.com/Sankalp-gupta1/TalentIQ-AI-Resume-Screening.git
cd TalentIQ-AI-Resume-Screening
```

Alternatively download the GitHub ZIP, extract it, and open the folder containing `docker-compose.yml` in a terminal.

## 3. Recommended Docker setup

### 3.1 Create private configuration

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env`, replace `JWT_SECRET_KEY` with a long unique random value, and keep `.env` private. Do not commit it.

### 3.2 Build and start

Run from the repository root:

```bash
docker compose up --build -d
docker compose ps
```

Services: Next.js frontend, FastAPI backend, PostgreSQL, Redis and a Celery worker scaffold.

### 3.3 Seed fictional demo records

```bash
docker compose exec backend python -m app.seed
```

| Role | Email | Password |
|---|---|---|
| Recruiter | `recruiter@talentiq.demo` | `TalentIQDemo!23` |
| Client | `client@talentiq.demo` | `TalentIQDemo!23` |

These credentials and profiles are fictional and local-demo-only. Do not use them in a hosted/production environment.

### 3.4 Local service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend root | http://localhost:8000 |
| Swagger / OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |

### 3.5 Useful commands

```bash
# Status and logs
docker compose ps
docker compose logs -f backend
docker compose logs -f

# Stop and preserve local data
docker compose down

# Start existing services
docker compose up -d

# WARNING: deletes local database and upload volumes
docker compose down -v

# Rebuild after clean reset
docker compose up --build -d
docker compose exec backend python -m app.seed
```

## 4. Optional OpenAI API key

The app runs without a key. Without it, job scorecards can be entered/edited manually and candidate matching uses the local deterministic rules scorer.

To enable optional job-description extraction:

1. Obtain an API key from your own OpenAI account.
2. Open the root `.env` file (not `.env.example`).
3. Set:

```dotenv
OPENAI_API_KEY=your_own_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

4. Save and restart the API:

```bash
docker compose restart backend
```

**Current key usage:** JD-to-scorecard extraction only. Candidate matching is rules-based and does not call an LLM.

Security:
- Never hardcode keys in source code.
- Never commit `.env`.
- Never expose private keys through frontend `NEXT_PUBLIC_` variables.
- Every operator must provide their own key and manage their own provider billing.
- Leave the value blank to use manual scorecard entry.

## 5. Direct local development without Docker

### 5.1 Backend with SQLite

Windows PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///./talentiq.db"
$env:JWT_SECRET_KEY = "replace-with-a-long-random-local-secret"
$env:CORS_ORIGINS = "http://localhost:3000"
uvicorn app.main:app --reload --port 8000
```

macOS/Linux:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./talentiq.db"
export JWT_SECRET_KEY="replace-with-a-long-random-local-secret"
export CORS_ORIGINS="http://localhost:3000"
uvicorn app.main:app --reload --port 8000
```

### 5.2 Seed demo records in a second terminal

Windows PowerShell:

```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "sqlite:///./talentiq.db"
$env:JWT_SECRET_KEY = "replace-with-a-long-random-local-secret"
python -m app.seed
```

macOS/Linux:

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="sqlite:///./talentiq.db"
export JWT_SECRET_KEY="replace-with-a-long-random-local-secret"
python -m app.seed
```

### 5.3 Start frontend in a third terminal

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then:

```bash
npm run dev
```

Open http://localhost:3000.

## 6. Environment variables

| Name | Required | Purpose |
|---|---|---|
| `APP_ENV` | No | Runtime label |
| `DATABASE_URL` | Yes | SQLAlchemy database URL |
| `JWT_SECRET_KEY` | Yes; replace placeholder | JWT signing secret |
| `JWT_ALGORITHM` | No | JWT algorithm (default HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime |
| `OPENAI_API_KEY` | No | Optional JD extraction key |
| `OPENAI_MODEL` | No | Model used for structured JD extraction |
| `REDIS_URL` | Worker use | Redis broker/backend URL |
| `CORS_ORIGINS` | Browser use | Comma-separated allowed browser origins |
| `MAX_UPLOAD_FILES` | No | Configured maximum file count per request |
| `NEXT_PUBLIC_API_URL` | Direct frontend run | API base URL in `frontend/.env.local` |

Never commit `.env`, `.env.local`, secrets, database dumps, uploads or real candidate files.

## 7. Tests and local checks

Backend:

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest -q
python -m compileall -q app
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

Unit tests do not establish full browser end-to-end coverage or production readiness.

## 8. Troubleshooting

- **Docker not found:** install/start Docker Desktop or Engine, open a fresh terminal and retry.
- **Frontend cannot reach API:** check `docker compose ps`, backend logs, API port 8000 and `CORS_ORIGINS`.
- **Port busy:** stop the process or change host-side port mapping and update frontend API/CORS settings.
- **PostgreSQL not ready:** inspect `docker compose logs postgres` and wait for its health check.
- **Demo login missing:** run the seed command again; reset volumes only if necessary (this deletes demo data).
- **OpenAI extraction unavailable:** manual scorecard entry still works; check private `.env` and restart backend.
- **Resume marked `needs_ocr`:** it likely contains scanned images; OCR is not included.

## 9. Scope and operational notes

- No hosted URL is supplied because no deployment has been performed.
- Upload processing is synchronous. `MAX_UPLOAD_FILES=500` is a configuration ceiling, not a performance guarantee.
- Redis/Celery is a worker foundation, not a complete queued bulk-processing pipeline.
- Candidate matching is deterministic and rules-based, not an LLM/ML CV-scoring model.
- Upload consent is a basic recruiter attestation, not a full consent-management lifecycle.
- Do not use real candidate data until security, privacy, storage, retention and legal reviews are complete.
