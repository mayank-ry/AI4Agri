# AI4Agri

Production-style MVP for AI-assisted precision agriculture.

## Apps

- `frontend/` - Next.js App Router UI.
- `backend/` - FastAPI API, Supabase integration, external data services, and ML inference.

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## Run Backend

```bash
pip install -r requirements.txt
cd backend
uvicorn main:app --reload
```

## Important Environment

Copy `.env.example` to `.env` and fill Supabase, Gemini, and optional GEE values.

## Active API

See `docs/api_spec.md`.
