# AI4Agri Architecture

AI4Agri is a hackathon MVP with a single active backend and a Next.js frontend.

## Runtime Shape

- Frontend: `frontend/src/app/*` using Next.js App Router.
- API client: `frontend/src/lib/api.ts`.
- Backend entrypoint: `backend/main.py`.
- Backend routes: `backend/routes/*`.
- Supabase helpers: `backend/database/*`.
- External data services: `backend/services/*`.
- ML and AI logic: `backend/ml/*`.

## Request Flow

1. User signs in with Supabase Auth from the frontend.
2. Frontend API client attaches the Supabase JWT.
3. FastAPI validates JWT with `database/auth_helper.py`.
4. Routes fetch farmer/field data through Supabase service helpers.
5. ML pipelines run locally from `backend/ml/cache` and `backend/ml/models`.

## ML Loading Policy

- Preload at startup: Flan-T5 chatbot fallback and intent classifier.
- Lazy-load: disease CNN, ViT backup, translation model.
- Model registry: `backend/ml/model_manager.py`.

## Preserved Features

- Disease detection with CNN plus ViT fallback.
- Gemini chatbot with local Flan-T5 fallback.
- Streaming chatbot endpoint.
- Health scoring with NDVI/weather/soil inputs.
- Irrigation recommendation via WSRI and RandomForest planner.
- Supabase auth, database, and storage integration.
