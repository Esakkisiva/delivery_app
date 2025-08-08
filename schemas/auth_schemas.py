from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re

# --- Base Schemas to Avoid Repetition ---

class PhoneNumberMixin(BaseModel):
    phone_number: str = Field(..., description="User's phone number, international format preferred.")

    @field_validator('phone_number')
    @classmethod
    def validate_and_clean_phone_number(cls, v: str) -> str:
        phone = re.sub(r'[^\d\+]', '', v)
        if not re.match(r'^\+?\d{10,15}$', phone):
            raise ValueError('Invalid phone number format.')
        return phone

# --- Request Schemas ---

class OTPRequest(PhoneNumberMixin):
    pass

class OTPVerify(PhoneNumberMixin):
    otp: str = Field(..., min_length=6, max_length=6, description="The 6-digit OTP.")

    @field_validator('otp')
    @classmethod
    def validate_otp_format(cls, v: str) -> str:
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
        from_attributes = True
