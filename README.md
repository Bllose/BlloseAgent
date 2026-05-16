# BlloseAgent

A multi-agent AI platform powered by **FastAPI + LangChain + LangGraph** (backend) and **Next.js 14** (frontend).

BlloseAgent runs a cluster of collaborative LLM agents coordinated by **SelfAgent**. The lead agent **bllose** handles intent recognition and user interaction, while specialist agents (**Coding Leader**, **Paper Leader**) execute delegated tasks. Communication uses a JSONL-based inbox message bus.

## Architecture

```
User → Frontend (Next.js) → SSE Stream → Backend (FastAPI)
                                              │
                                        AgentService
                                              │
                                         bllose (lead)
                                       /          \
                              handles simple     request_expert
                              tasks directly          │
                                               SelfAgent
                                             /          \
                                   Coding Leader    Paper Leader
```

### Agent Roles

| Agent | Role | Behavior |
|-------|------|----------|
| **self_agent** | cluster manager | Starts all sub-agents, runs polling loop, dispatches tasks, syncs status, owns token tracker |
| **bllose** | intent_recognition | Lead agent — interacts with user, classifies intent, handles simple tasks, delegates to experts |
| **Coding Leader** | coding_leader | Background ReAct agent — writes/edits code, runs shell commands, debugs |
| **Paper Leader** | paper_leader | Background ReAct agent — reads papers, summarizes research, answers academic questions |

Each expert agent runs a **LangGraph ReAct loop** (agent ↔ tools) in its own daemon thread, polling its JSONL inbox for tasks.

### Communication

Agents communicate via **JSONL inbox files** stored in `.team/inbox/{agent_name}.jsonl`. Send appends a line; read drains all lines.

```
bllose → request_expert → self_agent inbox → dispatch → Coding Leader inbox
Coding Leader → result → self_agent inbox → forward → bllose inbox
bllose reads inbox on next user message → relays result to user
```

Message types: `message`, `broadcast`, `task_assignment`, `status_report`, `shutdown_request`, `shutdown_response`.

### Token Tracking

**GlobalTokenTracker** (owned by SelfAgent) tracks per-agent and global token consumption using `tiktoken` for estimation and LLM response metadata for actual output counts. Stats are exposed via API and displayed on the frontend.

## Project Structure

```
backend/
  bllose_agent/
    main.py              FastAPI app + lifespan (start/stop SelfAgent)
    agent/
      base_agent.py      BaseAgent ABC + AgentStatus dataclass
      self_agent.py      Top-level cluster manager
      teammate.py        BlloseAgent, TeammateAgent, ReAct graph, tool factories
      intent/            Legacy intent-classification graph
      state.py           AgentState type
    api/
      chat.py            POST /api/chat/stream (SSE)
      agent.py           Agent status + token stats endpoints
      health.py          GET /api/health
      intent.py          Intent recognition endpoints
      router.py          API router aggregation
    services/
      agent_service.py   Runs bllose graph with astream_events v2 + token recording
      team_manager.py    MessageBus + TeammateManager (persisted config.json)
      token_tracker.py   GlobalTokenTracker + AgentTokenTracker
    config/settings.py   Pydantic Settings (Anthropic, embedding, server)
    models/              Pydantic request/response schemas
    tools/               Base tool definitions
  .team/
    config.json          Persisted agent registry + statuses
    inbox/*.jsonl        Per-agent message inboxes
  requirements.txt
  Makefile

frontend/
  src/
    app/
      home/page.tsx      Main page (chat + status tabs, global token badge)
      login/page.tsx
      register/page.tsx
    components/
      chat/              ChatPanel, ChatInput, ChatMessage
      status/            StatusPanel (agent cards with token stats)
      auth/              LoginForm, RegisterForm
    hooks/useAuth.ts     Auth state management
    lib/api.ts           Backend API client (SSE stream + REST)
    types/index.ts       TypeScript interfaces
  package.json
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY to your key
pip install -r requirements.txt
make run
# or: uvicorn bllose_agent.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

## API Reference

Once running, visit `http://localhost:8000/docs` for interactive Swagger UI.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/chat/stream` | POST | SSE chat stream with bllose agent |
| `/api/agent/info` | GET | Agent name, version, model |
| `/api/agent/status` | GET | Live status of all sub-agents |
| `/api/agent/status/{name}` | GET | Status of a single agent |
| `/api/agent/tokens` | GET | Token usage stats (per-agent + global) |
| `/api/intent/` | POST | Intent classification endpoints |

### SSE Stream Events

The `/api/chat/stream` endpoint yields these event types:

| Event | Description |
|-------|-------------|
| `text` | LLM text output token |
| `thinking` | LLM extended thinking content |
| `tool_start` | Tool invocation started (includes `name`) |
| `tool_end` | Tool invocation completed (includes `name`, `output`) |
| `error` | Processing error |
| `done` | Stream finished |

## Configuration

All settings via `.env` file. See `.env.example` for the full schema.

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | **Required.** Anthropic API key |
| `ANTHROPIC_BASE_URL` | — | Optional custom base URL |
| `LLM_MODEL` | `claude-sonnet-4-6` | Primary LLM model |
| `SMALL_LLM_MODEL` | — | Cheaper model for simple tasks (falls back to primary) |
| `LOGIC_LLM_MODEL` | — | Reasoning model (falls back to primary) |
| `EMBEDDING_LLM_MODEL` | `text-embedding-3-small` | Embedding model |
| `PORT` | `8000` | Backend port |
| `DEBUG` | `true` | Debug mode (CORS allows localhost) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | CORS origins for non-debug mode |
