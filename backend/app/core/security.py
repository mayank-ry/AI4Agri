from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

def create_access_token(subject: str | any, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token for authentication.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
