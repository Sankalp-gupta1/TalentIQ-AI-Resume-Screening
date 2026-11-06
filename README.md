# TalentIQ — AI-Assisted Resume Screening & Client Shortlist Portal

> **Full-stack take-home MVP · Local-first setup · No hosted deployment**  
> **GitHub:** https://github.com/Sankalp-gupta1/TalentIQ-AI-Resume-Screening

TalentIQ helps a staffing team organize job requirements, review PDF/DOCX resumes, compare candidate profiles against an editable scorecard, and share selected candidates with a client-facing review portal.

**Human-in-the-loop principle:** a match score is advisory only. It must never automatically reject a candidate or replace a recruiter's review of the original CV.

---

## Table of Contents

- [1. Product Overview](#1-product-overview)
- [2. Main Features](#2-main-features)
- [3. User Roles](#3-user-roles)
- [4. Technology Stack](#4-technology-stack)
- [5. Architecture](#5-architecture)
- [6. Project Structure](#6-project-structure)
- [7. Requirements](#7-requirements)
- [8. Quick Start with Docker](#8-quick-start-with-docker-recommended)
- [9. Demo Accounts and Sample Data](#9-demo-accounts-and-sample-data)
- [10. Optional OpenAI API Key](#10-optional-openai-api-key)
- [11. Run Without Docker](#11-run-without-docker)
- [12. Application Walkthrough](#12-application-walkthrough)
- [13. API Reference](#13-api-reference)
- [14. Tests and Verification](#14-tests-and-verification)
- [15. Environment Variables](#15-environment-variables)
- [16. Privacy, Fairness and Security](#16-privacy-fairness-and-security)
- [17. Known Limitations](#17-known-limitations)
- [18. Troubleshooting](#18-troubleshooting)
- [19. Stop and Reset](#19-stop-and-reset-the-application)
- [20. Future Improvements](#20-future-improvements)
- [21. Important Notes](#21-important-notes)

## 1. Product Overview

Recruiters often screen CVs manually, maintain shortlists in spreadsheets, and coordinate client feedback through disconnected messages. TalentIQ brings the main steps into one workspace:

1. A recruiter creates a job and reviews an editable scorecard.
2. The recruiter uploads PDF or DOCX resumes.
3. The system extracts selectable text, detects exact-file duplicates within the same job, and creates candidate profiles.
4. Candidates receive an explainable advisory match score with criterion-level evidence.
5. A recruiter reviews the original CV before sharing a candidate.
6. The client hiring manager sees only profiles submitted to that client and records a decision.
7. The recruiter follows candidate movement through a lightweight pipeline.

**Project status:** this repository contains a local-run portfolio/take-home MVP. It is not a hosted service, production ATS, or legal compliance certification. No cloud deployment is included.

## 2. Main Features

| Area | Included behavior |
|---|---|
| Job intake | Create a job from a description and populate an editable scorecard |
| Scorecard | Skills, experience range, location, notice-period limit and CTC fields |
| Resume upload | PDF/DOCX upload, per-file result reporting, 12 MB per-file limit |
| Parsing | Extract selectable PDF/DOCX text and common profile fields |
| Duplicate detection | SHA-256 exact-file duplicate detection within the same job |
| Matching | 0–100 advisory score with criterion-level evidence |
| Candidate discovery | Ranked list, profile search and evidence view |
| Client portal | Client sees only submitted candidates; email/phone and raw CV text are masked |
| Client feedback | Shortlist, reject with a reason, or propose an interview slot |
| Pipeline | Records screened, submitted and client decision events |
| Privacy foundation | Consent confirmation on upload, deletion endpoint and audit events |
| Authentication | JWT bearer tokens and Argon2 password hashing |
| Local infrastructure | Docker Compose, PostgreSQL, Redis, FastAPI and Next.js |

**AI distinction:** OpenAI is optional and currently used for job-description extraction into a draft scorecard. Candidate matching is a deterministic, evidence-based rules scorer. It is not a trained ML model or an LLM-generated CV score.

## 3. User Roles

### Recruiter
- Create and edit job scorecards.
- Upload candidate resumes after confirming the hiring-purpose consent condition.
- Review parsed profiles, scores and evidence.
- Search candidates and decide whom to submit.
- View pipeline and audit events; process deletion requests.

### Client hiring manager
- Review only profiles submitted to the client's tenant.
- See masked contact details and no raw CV text.
- Shortlist, reject with a reason, or propose an interview slot.

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Pydantic |
| ORM / data | SQLAlchemy 2, PostgreSQL 16, SQLite for direct local backend development |
| Migrations | Alembic |
| Resume extraction | PyMuPDF, python-docx |
| Matching | Explainable Python rules scorer |
| Optional LLM | OpenAI API for JD extraction |
| Authentication | JWT, Argon2 password hashing |
| Background foundation | Redis, Celery worker scaffold |
| Tests | pytest |
| Local orchestration | Docker Compose |

## 5. Architecture

```text
Recruiter / Client Browser
          | Next.js UI (localhost:3000)
          | REST + multipart requests
          v
FastAPI API (localhost:8000)
   |       |       +--> Optional OpenAI JD extraction
   |       +----------> PDF/DOCX text extraction
   |       +----------> Profile parsing + SHA-256 duplicate check
   |       +----------> Evidence-based rules scoring
   |       +----------> JWT role and client-tenant checks
   v
SQLAlchemy --> PostgreSQL (Docker) / SQLite (direct backend demo)
   +--> Users, jobs, candidates, scores, submissions
   +--> Pipeline events, consent fields, audit events

Redis + Celery worker: foundation for future asynchronous ingestion
```

## 6. Project Structure

```text
TalentIQ/
├── .env.example                 # Safe environment template
├── .gitignore
├── docker-compose.yml           # PostgreSQL, Redis, API, worker, frontend
├── README.md                    # This guide
├── TDD.md / TDD.pdf             # Technical design (Markdown + PDF)
├── deployment.md                # Local setup and environment guide
├── SECURITY.md                  # Responsible-use notes
├── .github/workflows/           # Backend test workflow
├── backend/
│   ├── Dockerfile, requirements.txt, alembic.ini
│   ├── migrations/
│   ├── app/                     # API, models, auth, parsing, scoring, seed
│   └── tests/                   # Resume parsing and scoring tests
└── frontend/
    ├── Dockerfile, package.json
    └── src/app + src/lib        # Next.js UI and API client
```

## 7. Requirements

### Recommended Docker setup

Install Git, Docker Desktop / Docker Engine with Docker Compose v2, and optionally VS Code. On Windows, start Docker Desktop with the WSL 2 backend enabled. Verify:

```bash
git --version
docker --version
docker compose version
```

### Direct development without Docker

- Python 3.12+
- Node.js 22+
- npm
- PostgreSQL/Redis only if not using SQLite for the backend-only local path

## 8. Quick Start with Docker (Recommended)

### Step 1 — Get the source

```bash
git clone https://github.com/Sankalp-gupta1/TalentIQ-AI-Resume-Screening.git
cd TalentIQ-AI-Resume-Screening
```

Alternatively, download the GitHub ZIP and extract it. Open the folder containing `docker-compose.yml` in a terminal. All Docker commands below run from this project root.

### Step 2 — Create a private environment file

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Open `.env`, replace `JWT_SECRET_KEY` with a long random value, and keep the file private. Leave `OPENAI_API_KEY` empty if you do not need optional JD extraction. Never upload `.env` to GitHub.

### Step 3 — Build and start services

```bash
docker compose up --build -d
docker compose ps
```

The first build may take several minutes while Docker downloads images and installs dependencies.

### Step 4 — Seed demo data

```bash
docker compose exec backend python -m app.seed
```

This creates fictional demo users, one Senior Java Developer requisition and three sample candidate profiles. The seed script avoids recreating the sample set when the demo recruiter already exists.

### Step 5 — Open the application

| Service | Address |
|---|---|
| Frontend | http://localhost:3000 |
| FastAPI root | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |

If the browser cannot connect immediately, wait for containers to start and check `docker compose ps` and `docker compose logs backend`.

## 9. Demo Accounts and Sample Data

All demo data is fictional and local-demo-only.

| Role | Email | Password |
|---|---|---|
| Recruiter | `recruiter@talentiq.demo` | `TalentIQDemo!23` |
| Client hiring manager | `client@talentiq.demo` | `TalentIQDemo!23` |

Sample requisition: **Senior Java Developer — Noida**, 5–8 years, Java/Spring Boot/Microservices, maximum notice 60 days.

| Candidate code | Profile | Experience | Skills | Notice |
|---|---|---:|---|---:|
| CND-91022 | Ritika Bansal — Senior Java Developer | 6.5 years | Java, Spring Boot, Microservices | 60 days |
| CND-91047 | Arjun Rawat — KYC Analyst | 3 years | KYC, AML, Excel | 30 days |
| CND-91088 | Pooja Nair — Java Developer | 4 years | Java, Hibernate, REST API | 90 days |

The small sample set is illustrative, not a benchmark dataset and not evidence of model quality or hiring fairness.

## 10. Optional OpenAI API Key

An API key is **not required** to start the app. Without it, recruiters can enter/edit scorecards manually and candidate matching uses the local rules scorer.

To enable optional job-description extraction:

1. Obtain your own key from your OpenAI account.
2. Open the private root `.env` file, not `.env.example`.
3. Set:

```dotenv
OPENAI_API_KEY=your_own_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

4. Save and restart the backend:

```bash
docker compose restart backend
```

The key is used for **JD extraction only** in this version. Candidate ranking remains deterministic and rules-based. Never hardcode a key in source code, commit `.env`, or expose a private key in a `NEXT_PUBLIC_` frontend variable. Each operator must use and secure their own key and manage their own provider billing. If the key is absent or invalid, use manual scorecard entry.

## 11. Run Without Docker

### 11.1 Backend with SQLite

**Windows PowerShell:**

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

**macOS / Linux:**

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

Keep this terminal running. API: `http://localhost:8000`.

### 11.2 Seed data

Open a second terminal from the repository root, then:

**Windows PowerShell:**

```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "sqlite:///./talentiq.db"
$env:JWT_SECRET_KEY = "replace-with-a-long-random-local-secret"
python -m app.seed
```

**macOS / Linux:**

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="sqlite:///./talentiq.db"
export JWT_SECRET_KEY="replace-with-a-long-random-local-secret"
python -m app.seed
```

### 11.3 Frontend

Open a third terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the UI:

```bash
npm run dev
```

Open `http://localhost:3000`. If you change the API port, update the frontend API URL and backend `CORS_ORIGINS`.

## 12. Application Walkthrough

1. Sign in as the recruiter.
2. Review the sample job or create a requisition.
3. Enter a job description; if the optional API key is configured, the backend can suggest structured fields. Otherwise enter them manually.
4. Review/edit the scorecard.
5. Upload PDF/DOCX CVs and confirm the hiring-purpose consent condition.
6. Review parsing results. Image-only/scanned files are marked `needs_ocr` and are not scored as empty CVs.
7. Inspect ranking and evidence. Do not use the score as an automatic rejection decision.
8. Review the original CV before submitting a candidate.
9. Sign in as the client hiring manager to review submitted candidates only.
10. Shortlist, reject with a reason, or propose an interview slot.
11. Return to the recruiter account to review pipeline and audit events.

## 13. API Reference

Interactive OpenAPI docs: `http://localhost:8000/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate and receive JWT |
| GET | `/api/v1/auth/me` | Current user and role |
| GET | `/api/v1/dashboard` | Dashboard counts |
| GET / POST | `/api/v1/jobs` | List or create jobs |
| PATCH | `/api/v1/jobs/{job_id}/scorecard` | Edit scorecard |
| POST | `/api/v1/jobs/{job_id}/resumes` | Upload PDF/DOCX resumes |
| GET | `/api/v1/jobs/{job_id}/candidates` | Ranked candidate list |
| GET | `/api/v1/candidates/{candidate_id}` | Role-aware candidate profile |
| POST | `/api/v1/candidates/{candidate_id}/submit` | Share candidate with client |
| GET | `/api/v1/client/submissions` | Client's submitted candidates |
| PATCH | `/api/v1/client/submissions/{submission_id}` | Client decision |
| GET | `/api/v1/pipeline` | Workflow history |
| DELETE | `/api/v1/candidates/{candidate_id}` | Recruiter deletion workflow |
| GET | `/api/v1/audit` | Recent audit events |

Use Swagger's **Authorize** control with the bearer token returned by `/api/v1/auth/login`.

## 14. Tests and Verification

Backend tests are under `backend/tests/`:

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest -q
python -m compileall -q app
```

Frontend build check:

```bash
cd frontend
npm install
npm run build
```

The repository includes a GitHub Actions backend-test workflow. Unit tests are not equivalent to full browser end-to-end tests, performance tests or a production security audit.

## 15. Environment Variables

| Variable | Required? | Purpose |
|---|---|---|
| `APP_ENV` | No | Runtime label |
| `DATABASE_URL` | Yes for configured DB | SQLAlchemy connection URL |
| `JWT_SECRET_KEY` | Yes; replace placeholder | JWT signing secret |
| `JWT_ALGORITHM` | No | JWT algorithm (default HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime |
| `OPENAI_API_KEY` | No | Optional JD extraction key |
| `OPENAI_MODEL` | No | Structured JD extraction model |
| `REDIS_URL` | Worker use | Redis broker URL |
| `CORS_ORIGINS` | Browser use | Allowed frontend origins |
| `MAX_UPLOAD_FILES` | No | Configured per-request file-count ceiling |
| `NEXT_PUBLIC_API_URL` | Direct frontend run | API base URL in `frontend/.env.local` |

## 16. Privacy, Fairness and Security

- Candidate names and contact details are not used by the scoring calculation.
- The rules scorer evaluates extracted skills, experience, notice period and location.
- Scores are advisory; there is no automatic rejection threshold.
- Recruiters should inspect the original CV before sharing a candidate.
- Client users are restricted to submissions associated with their `client_id`.
- Client profile responses mask email/phone and omit raw CV text.
- Candidate profile reads generate audit events.
- A recruiter deletion endpoint anonymizes selected fields and removes client submissions.
- Seed data is fictional. Do not upload real CVs to a public demo or public issue.

**Privacy limitation:** the upload confirmation is an MVP recruiter attestation, not a complete candidate-facing consent management system. Before real-world processing, implement verifiable consent, purpose notice, retention/deletion schedules, secure storage, malware scanning, access controls and legal review. This project is not a DPDP compliance certification.

## 17. Known Limitations

1. **OCR:** parser extracts selectable text; image-only PDFs are marked `needs_ocr`. OCR is not bundled.
2. **500-file scale:** configured request ceiling can be 500, but current uploads are processed synchronously. This is not verified as reliable production-scale 500-file ingestion.
3. **Scoring:** candidate matching is rules-based and explainable, not an LLM or trained ML model. Semantic skill equivalence is limited.
4. **Parsing:** resume layouts vary; extracted fields need recruiter review.
5. **Consent:** upload confirmation is not a full consent lifecycle.
6. **Storage:** local Docker volume is used. Production needs private encrypted object storage and malware scanning.
7. **Client workflow:** interview slots are text proposals; no calendar/email integration.
8. **Hardening:** rate limiting, token revocation, backup/restore, monitoring and comprehensive tenant-isolation tests remain future work.

## 18. Troubleshooting

### Docker command not found
Install/start Docker Desktop or Docker Engine, open a new terminal and retry `docker --version` and `docker compose version`.

### Frontend cannot reach backend
Run `docker compose ps` and `docker compose logs backend`. Confirm API port 8000 and `CORS_ORIGINS=http://localhost:3000`.

### Port 3000 or 8000 is busy
Stop the other process or change the host-side port mapping in `docker-compose.yml`; update the frontend API URL and CORS value if the API port changes.

### PostgreSQL is not ready
Inspect `docker compose logs postgres`, wait for the health check and then inspect/restart backend.

### Demo login does not work
Run `docker compose exec backend python -m app.seed`. If local state is inconsistent, reset local volumes as described below; this deletes demo data.

### OpenAI extraction is unavailable
Manual scorecard entry and rule-based matching still work. Check the private root `.env` and restart using `docker compose restart backend`. Never paste a key into public logs/issues.

### Resume shows `needs_ocr`
The file likely contains scanned images instead of selectable text. OCR is not part of this MVP.

## 19. Stop and Reset the Application

Stop containers and preserve volumes:

```bash
docker compose down
```

Start again:

```bash
docker compose up -d
```

Stop and permanently delete local database/upload volumes:

```bash
docker compose down -v
```

Rebuild and reseed after a clean reset:

```bash
docker compose up --build -d
docker compose exec backend python -m app.seed
```

## 20. Future Improvements

- Asynchronous ingestion with per-file progress, retries and dead-letter handling
- OCR for scanned resumes
- Section-aware parsing and recruiter correction UI
- Candidate-facing consent and withdrawal workflow
- Secure private object storage, malware scanning and retention automation
- Stronger authorization and tenant-isolation tests
- Weekly human review of ranking samples and fairness monitoring
- Evaluation dataset with recruiter-labelled examples
- Calendar, email and ATS integrations

## 21. Important Notes

- No live deployment is included. Run the project locally using this guide.
- Never commit `.env`, API keys, real CVs, personal data or production credentials.
- Use synthetic demo data for evaluation.
- Do not describe this MVP as a production-ready hiring decision system.
- See `TDD.pdf` for architecture/design and `deployment.md` for concise local setup/environment details.
- Read `SECURITY.md` before using the project beyond a local demo.
