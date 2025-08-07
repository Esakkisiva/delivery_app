# schemas.py (Compatible with Pydantic v1)

from pydantic import BaseModel, validator, Field
from datetime import datetime
import re

# --- Base Schemas to Avoid Repetition ---

class PhoneNumberMixin(BaseModel):
    phone_number: str = Field(..., description="User's phone number, international format preferred.")

    @validator('phone_number')
    def validate_and_clean_phone_number(cls, v):
        phone = re.sub(r'[^\d\+]', '', v)
        if not re.match(r'^\+?\d{10,15}$', phone):
            raise ValueError('Invalid phone number format.')
        return phone

# --- Request Schemas ---

class OTPRequest(PhoneNumberMixin):
    pass

class OTPVerify(PhoneNumberMixin):
    otp: str = Field(..., min_length=6, max_length=6, description="The 6-digit OTP.")

    @validator('otp')
    def validate_otp_format(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits.')
        return v

# --- Response Schemas ---

class LoginResponse(BaseModel):
    message: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    phone_number: str
    is_verified: bool
    created_at: datetime
    
    class Config:
        # Use orm_mode for Pydantic v1
        orm_mode = True