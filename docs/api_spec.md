# AI4Agri API Spec

Active FastAPI entrypoint: `backend/main.py`

Base URL: `http://localhost:8000`

## Health

- `GET /health` - API and ML model registry status.
- `GET /api/v1/health/{field_id}` - field health score, WSRI, CYAS, and raw NDVI/weather/soil inputs.

## Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Auth-protected endpoints expect `Authorization: Bearer <supabase_jwt>`.

## Disease Detection

- `POST /api/v1/disease/detect`
  - multipart fields: `field_id`, `image`
  - runs CNN first, falls back to ViT when confidence is low or CNN fails.
- `GET /api/v1/disease/history/{field_id}`
- `GET /api/v1/disease/models/status`

## Irrigation

- `POST /api/v1/irrigation/recommend`
  - JSON: `{ "field_id": "..." }`
- `PUT /api/v1/irrigation/{rec_id}/done`

## Chatbot

- `POST /api/v1/chatbot/message`
- `POST /api/v1/chatbot/message/stream`
- `GET /api/v1/chatbot/suggestions/{field_id}`
