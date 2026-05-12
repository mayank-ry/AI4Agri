from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.supabase_client import get_anon_db, db_insert, db_select_one
from database.auth_helper import verify_token, get_farmer_id
import os
import structlog

router = APIRouter(tags=["auth"])
log = structlog.get_logger()

class RegisterRequest(BaseModel):
    name: str
    phone: str
    email: str
    password: str
    district: str
    state: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(req: RegisterRequest):
    try:
        supabase = get_anon_db()
        # 1. Create Supabase auth user via anon client
        auth_response = supabase.auth.sign_up({
            "email": req.email, 
            "password": req.password
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Registration failed. Email might be in use.")
            
        user_id = auth_response.user.id
        
        # 3. Insert farmer profile to farmers table
        farmer_data = {
            "auth_user_id": user_id,
            "name": req.name,
            "phone": req.phone,
            "district": req.district,
            "state": req.state,
            "preferred_lang": "hi"
        }
        
        inserted_farmer = db_insert("farmers", farmer_data)
        
        # 4. Return session data and profile
        return {
            "success": True,
            "access_token": auth_response.session.access_token if auth_response.session else None,
            "farmer": inserted_farmer
        }
    except Exception as e:
        log.error("registration_failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@router.post("/login")  
def login(req: LoginRequest):
    try:
        supabase = get_anon_db()
        auth_response = supabase.auth.sign_in_with_password({
            "email": req.email, 
            "password": req.password
        })
        
        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Invalid login credentials")
            
        user_id = auth_response.user.id
        farmer_data = db_select_one("farmers", {"auth_user_id": user_id})
        
        return {
            "success": True,
            "access_token": auth_response.session.access_token,
            "farmer_data": farmer_data
        }
    except Exception as e:
        log.error("login_failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid email or password")

@router.get("/me")
def get_me(token: dict = Depends(verify_token)):
    try:
        farmer_id = get_farmer_id(token["sub"])
        farmer_data = db_select_one("farmers", {"id": farmer_id})
        if not farmer_data:
            raise HTTPException(status_code=404, detail="Farmer profile not found")
        return {"success": True, "farmer": farmer_data}
    except Exception as e:
        log.error("get_me_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch profile")
