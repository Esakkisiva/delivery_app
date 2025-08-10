from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets
import string
from jose import JWTError, jwt
from database import get_db
from models.auth_models import User
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/verify-otp")

def hash_otp(otp: str) -> str:
    """Hash OTP using passlib context"""
    return pwd_context.hash(otp)

def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify OTP against the hashed version"""
    return pwd_context.verify(plain_otp, hashed_otp)

def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> dict:
    """Get current user from JWT token and return phone_number dict for compatibility"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="User is not verified")
    
    return {"phone_number": user.phone_number, "user_id": user.id}