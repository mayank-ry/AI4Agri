from jose import jwt, JWTError
from fastapi import HTTPException, Header, status
import os
import structlog
from database.supabase_client import get_db

log = structlog.get_logger()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "PASTE_YOUR_SUPABASE_JWT_SECRET_HERE")

def verify_token(authorization: str = Header(...)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except JWTError as e:
        log.error("jwt_verification_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_farmer_id(user_id: str) -> str:
    db = get_db()
    response = db.table("farmers").select("id").eq("auth_user_id", user_id).limit(1).execute()
    
    if not response.data:
        log.error("farmer_not_found_for_user", user_id=user_id)
        raise HTTPException(status_code=404, detail="Farmer profile not found for this user.")
        
    return response.data[0]["id"]
