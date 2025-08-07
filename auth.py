# auth.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import secrets
import string
from dotenv import load_dotenv  # <-- 1. ADD THIS IMPORT

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()  # <-- 2. ADD THIS LINE TO LOAD THE .ENV FILE

# --- Configuration & Setup ---

# Use passlib for strong, flexible hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load configuration from environment
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# This tells FastAPI where the client should go to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/verify-otp")

# --- Hashing and OTP Functions ---

def hash_otp(otp: str) -> str:
    """Hash OTP using passlib context"""
    return pwd_context.hash(otp)

def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify OTP against the hashed version"""
    return pwd_context.verify(plain_otp, hashed_otp)

def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

# --- JWT Token Functions ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decode JWT token to get the current user. This is a dependency function.
    It will raise HTTPException if the token is invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
        # You can also add more data to the returned dictionary if needed
        return {"phone_number": phone_number}
    except JWTError:
        raise credentials_exception