from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re

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
    id: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
