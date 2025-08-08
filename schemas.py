# schemas.py (Corrected for Pydantic V2)

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

class AddressBase(BaseModel):
    country: str = Field(default="India")
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    flat_house_building: Optional[str] = None
    area_street_sector: Optional[str] = None
    landmark: Optional[str] = None
    pincode: Optional[str] = None
    town_city: Optional[str] = None
    state: Optional[str] = None

    @field_validator('mobile_number')
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        if v and not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v

    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        if v and not re.match(r'^\d{6}$', v):
            raise ValueError('Pincode must be exactly 6 digits')
        return v

class AddressCreate(AddressBase):
    full_name: str
    mobile_number: str
    flat_house_building: str
    area_street_sector: str
    pincode: str
    town_city: str
    state: str

class AddressUpdate(AddressBase):
    pass

class AddressResponse(AddressBase):
    # --- FIX: Changed id to 'str' to match the UUID from the model ---
    id: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True