from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.auth_models import User
from models.address_models import Address
from schemas.address_schemas import AddressCreate, AddressUpdate, AddressResponse
import auth
from database import get_db

router = APIRouter(
    prefix="/api/addresses",
    tags=["Addresses"]
)

@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address_for_current_user(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Create a new address for the currently authenticated user.
    """
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_address = Address(**address.model_dump(), owner_id=user.id)
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

@router.get("/", response_model=list[AddressResponse])
def get_addresses_for_current_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Get all addresses belonging to the currently authenticated user.
    """
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return db.query(Address).filter(Address.owner_id == user.id).all()

@router.put("/{address_id}", response_model=AddressResponse)
def update_user_address(
    address_id: int,
    update_data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Update an address belonging to the currently authenticated user.
    """
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    address = db.query(Address).filter(Address.id == address_id).first()

    if not address or address.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Delete an address belonging to the currently authenticated user.
    """
    phone_number = current_user.get("phone_number")
    user = db.query(User).filter(User.phone_number == phone_number).first()

    address = db.query(Address).filter(Address.id == address_id).first()

    if not address or address.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
        
    db.delete(address)
    db.commit()
    return None
