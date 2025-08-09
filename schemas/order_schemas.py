from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional
from enum import Enum

class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Order Item Schemas
class OrderItemCreate(BaseModel):
    menu_item_id: int = Field(..., description="ID of the menu item")
    quantity: int = Field(..., ge=1, description="Quantity of the item")
    special_instructions: Optional[str] = Field(None, description="Special instructions for the item")

class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    item_name: str
    item_price: float
    quantity: int
    special_instructions: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Order Schemas
class OrderCreate(BaseModel):
    delivery_address_id: str = Field(..., description="ID of the delivery address")
    delivery_instructions: Optional[str] = Field(None, description="Special delivery instructions")
    order_items: List[OrderItemCreate] = Field(..., min_items=1, description="List of items to order")

class OrderUpdate(BaseModel):
    status: Optional[OrderStatusEnum] = Field(None, description="New order status")
    delivery_instructions: Optional[str] = Field(None, description="Updated delivery instructions")
    delivery_agent_id: Optional[int] = Field(None, description="ID of assigned delivery agent")

class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_id: int
    delivery_address_id: str
    delivery_agent_id: Optional[int]
    status: OrderStatusEnum
    total_amount: float
    delivery_fee: float
    tax_amount: float
    subtotal: float
    estimated_delivery_time: Optional[datetime]
    actual_delivery_time: Optional[datetime]
    delivery_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    customer: Optional[dict] = None
    delivery_address: Optional[dict] = None
    delivery_agent: Optional[dict] = None
    order_items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    size: int

# Order Summary for listing
class OrderSummary(BaseModel):
    id: str
    order_number: str
    status: OrderStatusEnum
    total_amount: float
    created_at: datetime
    estimated_delivery_time: Optional[datetime]
    
    class Config:
        from_attributes = True
