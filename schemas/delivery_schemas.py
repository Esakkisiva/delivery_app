from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum
import re
from .order_schemas import OrderStatusEnum

class DeliveryAgentStatusEnum(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    OFFLINE = "offline"

# Delivery Agent Schemas
class DeliveryAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the delivery agent")
    phone: str = Field(..., description="Phone number of the delivery agent")
    email: Optional[str] = Field(None, description="Email address of the delivery agent")
    vehicle_type: Optional[str] = Field(None, description="Type of vehicle (bike, car, etc.)")
    vehicle_number: Optional[str] = Field(None, description="Vehicle registration number")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Phone number must be exactly 10 digits')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class DeliveryAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    current_status: Optional[DeliveryAgentStatusEnum] = Field(None)
    current_latitude: Optional[float] = Field(None, ge=-90, le=90)
    current_longitude: Optional[float] = Field(None, ge=-180, le=180)
    vehicle_type: Optional[str] = Field(None)
    vehicle_number: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^\d{10}$', v):
            raise ValueError('Phone number must be exactly 10 digits')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Current latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Current longitude")

class DeliveryAgentResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str]
    current_status: DeliveryAgentStatusEnum
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    last_location_update: Optional[datetime]
    is_active: bool
    vehicle_type: Optional[str]
    vehicle_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DeliveryAgentListResponse(BaseModel):
    delivery_agents: list[DeliveryAgentResponse]
    total: int
    page: int
    size: int

# Delivery Assignment Schemas
class DeliveryAssignment(BaseModel):
    order_id: str = Field(..., description="ID of the order to assign")
    delivery_agent_id: int = Field(..., description="ID of the delivery agent to assign")

class DeliveryStatusUpdate(BaseModel):
    order_id: str = Field(..., description="ID of the order")
    status: OrderStatusEnum = Field(..., description="New delivery status")
    estimated_delivery_time: Optional[datetime] = Field(None, description="Updated estimated delivery time")
