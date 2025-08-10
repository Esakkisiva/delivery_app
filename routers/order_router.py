from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

# Import local modules
from models.auth_models import User
from models.address_models import Address
from models.order_models import Order, OrderItem, OrderStatus
from schemas.order_schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse, 
    OrderSummary, OrderItemCreate, OrderItemResponse
)
import auth
from database import get_db
from sms_service import sms_service

router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)

def generate_order_number() -> str:
    """Generate a unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    random_suffix = str(uuid.uuid4())[:3]
    return f"ORD{timestamp}{random_suffix}"

def calculate_order_totals(order_items: List[OrderItemCreate], db: Session) -> tuple[float, float, float, float]:
    """Calculate order totals including tax and delivery fee"""
    subtotal = 0.0
    
    # Note: This function assumes menu items exist in the restaurant system
    # The actual menu item lookup should be done through the restaurant API
    # For now, we'll use a placeholder approach that can be updated when integrated
    
    for item in order_items:
        # Placeholder: In production, this should call the restaurant API
        # or use a shared database to get menu item details
        # For now, we'll use a default price - this should be replaced with actual integration
        default_price = 100.0  # This should come from restaurant system
        subtotal += default_price * item.quantity
    
    # Calculate tax (assuming 5% GST)
    tax_amount = subtotal * 0.05
    
    # Calculate delivery fee (assuming flat rate)
    delivery_fee = 50.0 if subtotal < 500 else 0.0
    
    # Calculate total
    total_amount = subtotal + tax_amount + delivery_fee
    
    return subtotal, tax_amount, delivery_fee, total_amount

def build_order_response_data(order: Order) -> dict:
    """Helper function to build order response data without problematic relationships"""
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "delivery_address_id": order.delivery_address_id,
        "delivery_agent_id": order.delivery_agent_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "delivery_fee": order.delivery_fee,
        "tax_amount": order.tax_amount,
        "subtotal": order.subtotal,
        "estimated_delivery_time": order.estimated_delivery_time,
        "actual_delivery_time": order.actual_delivery_time,
        "delivery_instructions": order.delivery_instructions,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "delivery_address": None,  # We'll handle this separately if needed
        "customer": None,  # We'll handle this separately if needed
        "delivery_agent": None,  # We'll handle this separately if needed
        "order_items": [OrderItemResponse.model_validate(item) for item in order.order_items]
    }

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Create a new order for the authenticated user"""
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify delivery address belongs to user
    address = db.query(Address).filter(
        Address.id == order_data.delivery_address_id,
        Address.owner_id == user.id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Delivery address not found or doesn't belong to user"
        )
    
    # Calculate order totals
    subtotal, tax_amount, delivery_fee, total_amount = calculate_order_totals(order_data.order_items, db)
    
    # Create order
    order_number = generate_order_number()
    db_order = Order(
        order_number=order_number,
        customer_id=user.id,
        delivery_address_id=order_data.delivery_address_id,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        delivery_fee=delivery_fee,
        tax_amount=tax_amount,
        subtotal=subtotal,
        delivery_instructions=order_data.delivery_instructions,
        estimated_delivery_time=datetime.now(timezone.utc) + timedelta(minutes=45)
    )
    
    db.add(db_order)
    db.flush()  # Get the order ID
    
    # Create order items
    for item_data in order_data.order_items:
        # Placeholder: In production, this should fetch menu item details from restaurant system
        # For now, we'll use placeholder data - this should be replaced with actual integration
        placeholder_item_name = f"Menu Item {item_data.menu_item_id}"
        placeholder_item_price = 100.0  # This should come from restaurant system
        
        db_order_item = OrderItem(
            order_id=db_order.id,
            menu_item_id=item_data.menu_item_id,
            item_name=placeholder_item_name,
            item_price=placeholder_item_price,
            quantity=item_data.quantity,
            special_instructions=item_data.special_instructions
        )
        db.add(db_order_item)
    
    db.commit()
    db.refresh(db_order)
    
    # Send order confirmation SMS
    # TEMPORARILY DISABLED FOR TESTING
    # sms_service.send_order_status_sms(
    #     to_number="+919342044743",  # TEMPORARILY HARDCODED FOR TESTING
    #     order_id=db_order.id,
    #     status="pending",
    #     order_number=order_number
    # )
    
    # Convert to response model to ensure proper serialization
    response_data = build_order_response_data(db_order)
    return OrderResponse.model_validate(response_data)

@router.get("/", response_model=OrderListResponse)
async def get_user_orders(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get orders for the authenticated user with pagination and filtering"""
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Build query
    query = db.query(Order).filter(Order.customer_id == user.id)
    
    # Apply status filter
    if status_filter:
        try:
            order_status = OrderStatus(status_filter)
            query = query.filter(Order.status == order_status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return OrderListResponse(
        orders=[OrderResponse.model_validate(build_order_response_data(order)) for order in orders],
        total=total,
        page=page,
        size=size
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get detailed information about a specific order"""
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.customer_id == user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    response_data = build_order_response_data(order)
    return OrderResponse.model_validate(response_data)

@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update order status and details (admin/restaurant use)"""
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.customer_id == user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Store old status for SMS notification
    old_status = order.status
    
    # Update order fields
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    # Update timestamp
    order.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(order)
    
    # Send SMS notification if status changed
    if order_update.status and order_update.status != old_status:
        sms_service.send_order_status_sms(
            to_number="+919342044743",  # TEMPORARILY HARDCODED FOR TESTING
            order_id=order.id,
            status=order_update.status.value,
            order_number=order.order_number
        )
    
    response_data = build_order_response_data(order)
    return OrderResponse.model_validate(response_data)

@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Cancel an order (only if it's still pending or confirmed)"""
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.customer_id == user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check if order can be cancelled
    if order.status in [OrderStatus.DISPATCHED, OrderStatus.DELIVERED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be cancelled at this stage"
        )
    
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already cancelled"
        )
    
    # Cancel the order
    order.status = OrderStatus.CANCELLED
    order.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(order)
    
    # Send cancellation SMS
    sms_service.send_order_status_sms(
        to_number="+919342044743",  # TEMPORARILY HARDCODED FOR TESTING
        order_id=order.id,
        status="cancelled",
        order_number=order.order_number
    )
    
    response_data = build_order_response_data(order)
    return OrderResponse.model_validate(response_data)
