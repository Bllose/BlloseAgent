# BlloseAgent

A full-stack AI Agent application.

## Structure

- `frontend/` — Next.js (React + TypeScript) UI
- `backend/` — FastAPI (Python + LangChain + LangGraph) API

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Docs

Once the backend is running, visit `http://localhost:8000/docs` for Swagger UI.
