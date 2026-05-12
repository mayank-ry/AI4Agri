from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
import structlog
import json
from database.supabase_client import db_select_one, get_db
from database.auth_helper import verify_token, get_farmer_id
from ml.inference_services import get_intent_service, get_flan_t5_service
from ml.prompt_templates import chat_system_prompt

router = APIRouter(tags=["chatbot"])
log = structlog.get_logger()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_gemini_model = None

if GEMINI_API_KEY and "PASTE" not in GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        log.info("gemini_model_ready")
    except Exception as e:
        log.error("gemini_init_failed", error=str(e))


class ChatRequest(BaseModel):
    message: str
    field_id: str
    lang: str = "hi"


def _build_system_prompt(field: dict, health_data: dict, farmer: dict) -> str:
    """Delegate to the centralized prompt template builder."""
    return chat_system_prompt(field, health_data, farmer)


@router.post("/message")
async def chat(req: ChatRequest, token: dict = Depends(verify_token)):
    farmer_id = get_farmer_id(token["sub"])

    # 1. Fetch context from DB
    field = db_select_one("fields", {"id": req.field_id, "farmer_id": farmer_id})
    if not field:
        # For testing: use mock field
        field = {
            "id": req.field_id,
            "crop_type": "गेहूं",
            "growth_stage": "vegetative",
        }

    db = get_db()
    try:
        health_resp = (
            db.table("health_scores")
            .select("*")
            .eq("field_id", req.field_id)
            .order("calculated_at", desc=True)
            .limit(1)
            .execute()
        )
        health_data = health_resp.data[0] if health_resp.data else {}
    except:
        health_data = {}

    try:
        farmer = db_select_one("farmers", {"id": farmer_id}) or {}
    except:
        farmer = {}

    # 2. Classify intent using local service
    intent_service = get_intent_service()
    intent_data = intent_service.classify(req.message)
    log.info("chat_intent", intent=intent_data["intent"])

    # 3. Try Gemini first
    ai_response = None
    model_used = "gemini"

    if _gemini_model:
        try:
            system = _build_system_prompt(field, health_data, farmer)
            prompt = f"{system}\n\nFarmer: {req.message}"
            response = _gemini_model.generate_content(prompt)
            ai_response = response.text
        except Exception as e:
            log.error("gemini_chat_failed", error=str(e))
            ai_response = None

    # 4. Fallback: Flan-T5 (local) if Gemini fails
    if not ai_response:
        model_used = "flan_t5_fallback"
        try:
            lang = "hi" if (any(ord(c) > 2300 for c in req.message) or req.lang == "hi") else "en"
            flan_service = get_flan_t5_service()
            ai_response = flan_service.generate_advice(
                crop=field.get("crop_type", "fasal"),
                stage=field.get("growth_stage", "vegetative"),
                issue=req.message,
                weather=f"Health:{health_data.get('achs_score','N/A')}",
                lang=lang,
            )
        except Exception as e:
            log.error("flan_t5_fallback_failed", error=str(e))
            ai_response = "कृपया बाद में प्रयास करें।"

    # 5. If HIGH urgency — add urgent prefix
    if intent_data["priority"] == "HIGH":
        ai_response = f"⚠️ {intent_data['priority_hi']}\n\n{ai_response}"

    return {
        "response": ai_response,
        "intent": intent_data["intent"],
        "priority": intent_data["priority"],
        "model_used": model_used,
    }


@router.post("/message/stream")
async def chat_stream(req: ChatRequest, token: dict = Depends(verify_token)):
    """Streaming version of chat — yields text chunks as they arrive."""
    try:
        farmer_id = get_farmer_id(token["sub"])
    except:
        # For testing, use test farmer ID
        farmer_id = "test-farmer-123"
        log.warning("streaming_auth_failed_using_test_mode")

    # 1. Fetch context from DB
    field = db_select_one("fields", {"id": req.field_id, "farmer_id": farmer_id})
    if not field:
        # For testing, create a mock field
        field = {
            "id": req.field_id,
            "crop_type": "गेहूं",
            "growth_stage": "vegetative",
            "area_hectares": 5,
        }
        log.warning("field_not_found_using_mock", field_id=req.field_id)

    db = get_db()
    try:
        health_resp = (
            db.table("health_scores")
            .select("*")
            .eq("field_id", req.field_id)
            .order("calculated_at", desc=True)
            .limit(1)
            .execute()
        )
        health_data = health_resp.data[0] if health_resp.data else {}
    except:
        health_data = {"achs_score": "N/A", "wsri_score": "N/A"}
        log.warning("health_data_fetch_failed_using_mock")

    try:
        farmer = db_select_one("farmers", {"id": farmer_id}) or {}
    except:
        farmer = {"farmer_name": "किसान", "region": "भारत"}
        log.warning("farmer_data_fetch_failed_using_mock")

    # 2. Classify intent
    intent_service = get_intent_service()
    intent_data = intent_service.classify(req.message)
    log.info("chat_stream_intent", intent=intent_data["intent"])

    async def generate():
        ai_response = None
        model_used = "gemini"

        # Try Gemini with streaming
        if _gemini_model:
            try:
                system = _build_system_prompt(field, health_data, farmer)
                prompt = f"{system}\n\nFarmer: {req.message}"
                response = _gemini_model.generate_content(prompt, stream=True)
                
                # Stream text chunks
                for chunk in response:
                    if chunk.text:
                        yield f"data: {json.dumps({'delta': chunk.text})}\n\n"
                
                ai_response = response.text if hasattr(response, 'text') else ""
            except Exception as e:
                log.error("gemini_stream_failed", error=str(e))
                ai_response = None

        # Fallback to Flan-T5 (local)
        if not ai_response:
            model_used = "flan_t5_fallback"
            try:
                lang = "hi" if (any(ord(c) > 2300 for c in req.message) or req.lang == "hi") else "en"
                flan_service = get_flan_t5_service()
                ai_response = flan_service.generate_advice(
                    crop=field.get("crop_type", "fasal"),
                    stage=field.get("growth_stage", "vegetative"),
                    issue=req.message,
                    weather=f"Health:{health_data.get('achs_score','N/A')}",
                    lang=lang,
                )
                # Stream fallback response word by word
                for word in ai_response.split():
                    yield f"data: {json.dumps({'delta': word + ' '})}\n\n"
            except Exception as e:
                log.error("flan_stream_fallback_failed", error=str(e))
                ai_response = "कृपया बाद में प्रयास करें।"
                yield f"data: {json.dumps({'delta': ai_response})}\n\n"

        # Send metadata at end
        metadata = {
            "response": ai_response,
            "intent": intent_data["intent"],
            "model_used": model_used,
        }
        yield f"data: {json.dumps(metadata)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/suggestions/{field_id}")
async def get_suggestions(field_id: str, token: dict = Depends(verify_token)):
    farmer_id = get_farmer_id(token["sub"])
    field = db_select_one("fields", {"id": field_id, "farmer_id": farmer_id})
    crop = field.get("crop_type", "fasal") if field else "fasal"

    return {
        "success": True,
        "suggestions": [
            f"Meri {crop} ki health abhi kaisi hai?",
            f"Kya mujhe apni {crop} mein aaj paani dena chahiye?",
            f"{crop} mein kaun si bimari lag sakti hai is mausam mein?",
            f"Khad kab aur kitna daalein?",
            f"Is hafte fasal ka kya dhyan rakhna chahiye?",
        ],
    }
