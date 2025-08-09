from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime
from typing import Optional
import re

# --- Base Schemas to Avoid Repetition ---
class PhoneNumberMixin(BaseModel):
    phone_number: str = Field(..., description="User's phone number, international format preferred.")

    @validator('phone_number')
    def validate_and_clean_phone_number(cls, v: str) -> str:
        phone = re.sub(r'[^\d\+]', '', v)
        if not re.match(r'^\+?\d{10,15}$', phone):
            raise ValueError('Invalid phone number format.')
        return phone

# --- Request Schemas ---
class OTPRequest(PhoneNumberMixin):
    pass

class OTPVerifyRequest(PhoneNumberMixin):
    otp: str = Field(..., min_length=6, max_length=6, description="The 6-digit OTP.")

    @validator('otp')
    def validate_otp_format(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('OTP must contain only digits.')
        return v

# Keep old name for compatibility
OTPVerify = OTPVerifyRequest

# --- Response Schemas ---
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginResponse(BaseModel):
    message: str
    phone_number: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    phone_number: str
    is_verified: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    phone_number: str
    is_verified: bool
    created_at: datetime
    
    # This is the single, correct way to configure in Pydantic V2
    model_config = ConfigDict(from_attributes=True)
