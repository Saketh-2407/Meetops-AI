# MeetOps AI — Agentic Meeting Assistant

An AI-powered meeting assistant that turns transcripts and audio recordings into summaries, decisions, action items, email drafts, and calendar suggestions — and then **asks for your approval before doing anything**.

> **Human-in-the-loop by design.** The agent never sends emails or creates calendar events automatically. Every action requires explicit approval.

---

## How It Works

```
Upload transcript or audio
         |
         v
  [Transcription]   <-- OpenAI (audio only)
         |
         v
  [Summary Agent]   --> title, key points, risks
         |
  [Decision Agent]  --> decisions + reasoning
         |
  [Action Agent]    --> tasks, owners, deadlines
         |
  [Email Agent]     --> follow-up email draft
         |
  [Calendar Agent]  --> meetings to schedule
         |
         v
  *** HUMAN APPROVAL ***  <-- you approve / reject each action
         |
         v
  [Execute Actions]
    - GitHub issues   (engineering tasks)
    - Gmail drafts    (email, never auto-sent)
    - Calendar events
         |
         v
  [Final Report + Audit Log saved to PostgreSQL]
```

---

## Features

- **Audio or text input** — upload an `.mp3` / `.wav` / `.m4a` or paste a transcript directly
- **Multi-agent pipeline** — 6 specialized agents, each with a focused job and validated Pydantic output schema
- **Real human-in-the-loop** — uses LangGraph `interrupt()` + PostgreSQL checkpointer to genuinely pause and resume mid-workflow
- **Tool execution** — creates GitHub issues, Gmail drafts, and Google Calendar events for approved actions
- **Full audit trail** — every action (approved or rejected) is logged to the database
- **Graceful degradation** — Google/GitHub integrations are optional; the core pipeline works without them

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Agent orchestration | LangGraph |
| AI / LLM | OpenAI (Responses API + structured outputs) |
| Data validation | Pydantic v2 |
| Database | PostgreSQL + SQLAlchemy |
| Frontend | Streamlit |
| Containerisation | Docker + Docker Compose |
| External tools | Gmail API, Google Calendar API, GitHub REST API |

---

## Project Structure

```
meetops-ai/
├── backend/
│   ├── app/
│   │   ├── agents/               # LangGraph nodes (one file per agent)
│   │   │   ├── graph.py          # pipeline wiring + checkpointer
│   │   │   ├── state.py          # MeetingState TypedDict
│   │   │   ├── summary_agent.py
│   │   │   ├── decision_agent.py
│   │   │   ├── action_agent.py
│   │   │   ├── email_agent.py
│   │   │   ├── calendar_agent.py
│   │   │   ├── approval_agent.py # interrupt() + execute_actions
│   │   │   └── final_report_agent.py
│   │   ├── schemas/              # Pydantic output schemas per agent
│   │   ├── services/             # openai_client, transcription, executor, google_auth
│   │   ├── models/               # SQLAlchemy DB models
│   │   ├── utils/prompts.py      # all prompt text in one place
│   │   ├── config.py             # env-driven settings
│   │   ├── database.py           # engine, session, persistence helpers
│   │   └── main.py               # FastAPI app + lifespan
│   ├── scripts/
│   │   └── google_oauth_setup.py # one-time Google OAuth consent flow
│   ├── Dockerfile
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── streamlit_app.py          # 3-phase UI: input → approval → results
├── sample_data/                  # sample transcripts for testing
├── tests/
│   ├── run_evaluation.py         # precision/recall eval harness
│   └── evaluation_set.json       # labelled test cases
├── docker-compose.yml
├── start_demo.bat                # Windows: one-command start
└── stop_demo.bat                 # Windows: one-command stop
```

---

## Prerequisites

- **Docker Desktop** — runs the database and backend
- **Python 3.11+** — for the Streamlit frontend
- **OpenAI API key** — required
- **Google OAuth credentials** — optional (enables Gmail drafts + Calendar events)
- **GitHub Personal Access Token** — optional (enables GitHub issue creation)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Saketh-2407/agentic-meeting-assistant.git
cd agentic-meeting-assistant
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in your values:

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/meetops
MODEL_NAME=gpt-4o-mini
TRANSCRIBE_MODEL=gpt-4o-transcribe

# Optional — leave blank to skip these integrations
GITHUB_TOKEN=
GITHUB_REPO=owner/repo
CALENDAR_TIMEZONE=Asia/Calcutta
```

### 3. (Optional) Set up Google OAuth

Required only for Gmail draft creation and Google Calendar events.

```bash
cd backend
pip install -r requirements.txt
python scripts/google_oauth_setup.py
```

This opens a browser consent flow once and saves the token to `backend/credentials/google_token.json`. The credentials folder is gitignored and never committed.

---

## Running the App

### Option A — One command (Windows)

```bat
start_demo.bat
```

The script checks for port conflicts, starts the Docker stack, waits for the backend health check, and launches Streamlit. Open **http://localhost:8501**.

To stop everything:

```bat
stop_demo.bat
```

### Option B — Manual (any OS)

**Terminal 1 — database + backend:**

```bash
docker compose up
```

Wait for: `Application startup complete.`

**Terminal 2 — frontend:**

```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open **http://localhost:8501**.

---

## Using the App

| Phase | What you do |
|---|---|
| **1. Input** | Paste a transcript or upload an audio file, click **Analyze Meeting** |
| **2. Approval** | Review each proposed action, approve or reject individually, click **Submit Approvals** |
| **3. Results** | See executed actions, the final meeting report, and the full audit log |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/analyze` | Run pipeline on a transcript — returns `thread_id` + pending actions |
| `POST` | `/resume` | Submit approval decisions and execute approved actions |
| `POST` | `/upload-transcript` | Upload a `.txt` file |
| `POST` | `/upload-audio` | Upload audio — transcribes then analyzes |

Interactive docs: **http://localhost:8000/docs**

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `MODEL_NAME` | Yes | `gpt-4o-mini` | Chat/reasoning model |
| `TRANSCRIBE_MODEL` | Yes | `gpt-4o-transcribe` | Audio transcription model |
| `GOOGLE_CREDENTIALS_PATH` | No | `credentials/google_credentials.json` | Google OAuth client secret |
| `GOOGLE_TOKEN_PATH` | No | `credentials/google_token.json` | Cached Google OAuth token |
| `GITHUB_TOKEN` | No | — | GitHub PAT with Issues read/write |
| `GITHUB_REPO` | No | — | Target repo as `owner/name` |
| `CALENDAR_TIMEZONE` | No | `Asia/Calcutta` | IANA timezone for Calendar events |
| `CALENDAR_DEFAULT_DURATION_MINUTES` | No | `60` | Default event duration |

---

## Security Notes

- `backend/.env` is gitignored — never committed
- `backend/credentials/` is gitignored — OAuth tokens never committed
- The Gmail integration calls `drafts.create` only — `messages.send` is never called
- All secrets are injected at runtime via environment variables or volume mounts
