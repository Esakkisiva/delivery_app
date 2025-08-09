from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
# Import the centralized settings object
from config import settings

class TokenData(BaseModel):
    id: Optional[str] = None

# --- TOKEN CREATION ---
def create_access_token(data: dict):
    to_encode = data.copy()
    # Use expire time from settings
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Use secret key and algorithm from settings
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    # Use expire time from settings
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    # Use secret key and algorithm from settings
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- TOKEN VERIFICATION ---
def verify_token(token: str, credentials_exception):
    try:
        # Use secret key and algorithm from settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # In JWT, the standard claim for the subject (user identifier) is 'sub'
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # You can return the whole payload if you need more data
        return TokenData(id=user_id)
    except JWTError:
        raise credentials_exception